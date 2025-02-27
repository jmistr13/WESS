#include "stm32f4xx.h"
#include "stm32f4xx_usart.h"
#include "stm32f4xx_gpio.h"
#include "stm32f4xx_adc.h"
#include "stm32f4xx_rcc.h"
#include "stm32f4xx_dma.h"
#include "stm32f4_discovery.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

//Global variables to store current gas reading data (these may change after each ADC reading)
float CO_val;
float NH3_val;
float NO2_val;
float TDS_val;
float ec25_val;
float ec_val;
float PC4_Voltage;
float Average_Hourly_CO;
float Average_Hourly_NH3;
float Average_Hourly_NO2;
float Average_Hourly_TDS;

char* sensor_name = "prototype";
float latitude  = 47.653132;
float longitude = -122.306114;

uint16_t NH3baseR;
uint16_t NO2baseR;
uint16_t CO_baseR;

// Max ADC resolution is 4096 (12-bit)
#define MAX_DIGITS 4
#define NUM_READINGS 3
#define MAX_CHARS 240
#define SECONDS 5
#define ADC_RANGE 4096
#define V_REF 5
#define KVALUE 1
#define TDS_FACTOR 0.5
#define WATER_TEMPERATURE 25                    //Assuming room temp water 25 deg C - more accurate readings can be made if we actually took water temps
#define DATA_POINTS_PER_HOUR 450                //Current implementation takes new samples every 8 seconds... 3600 seconds in an hour so 3600/9 = 450 samples per hour

int samples_taken = 0;                          //This keeps track of how many samples have been taken since system startup

float  CO_DataPoints[DATA_POINTS_PER_HOUR];       //Buffer of size DATA_POINTS_PER_HOUR to store DATA_POINTS_PER_HOUR CO values
float NH3_DataPoints[DATA_POINTS_PER_HOUR];       //Buffer of size DATA_POINTS_PER_HOUR to store DATA_POINTS_PER_HOUR NH3 values
float NO2_DataPoints[DATA_POINTS_PER_HOUR];       //Buffer of size DATA_POINTS_PER_HOUR to store DATA_POINTS_PER_HOUR NO2 values
float TDS_DataPoints[DATA_POINTS_PER_HOUR];       //Buffer of size DATA_POINTS_PER_HOUR to store DATA_POINTS_PER_HOUR TDS values

uint16_t gas_readings[NUM_READINGS];             //Buffer of size 3 to hold CO, NH3, NO2 values
uint16_t water_readings[NUM_READINGS-1];         //Buffer of size 2 to hold TDS and TURB values

enum channel {
  CH_NH3, CH_NO2, CH_CO
};
typedef enum channel channel_t;

// Enum for proper gas declaration
enum gas {
  CO, NO2, NH3
};

typedef enum gas gas_t;

/* Configure clocks for USART3 (DO NOT use USART1, it has a capacitor which
   garbles the output), Port C, Port B, and ADC1.
*/
void configure_rcc(void) {
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);      // Init USART3 clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);       // Init GPIOC clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);       // Init GPIOB clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);       // Init GPIOA clock

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE);        // init ADC1 clock
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC2, ENABLE);        // init ADC2 clock
}

/* Configure GPIO pins 10 and 11 for Port C and pin 1 for Port B
*/
void configure_gpio(void) {
    GPIO_InitTypeDef GPIO_InitStruct;
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_10 | GPIO_Pin_11;               // Pin PC10, connect to RX of RYLR998
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AF;                           // Pin PC11, connect to TX of RYLR998
    GPIO_InitStruct.GPIO_OType = GPIO_OType_PP;
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_UP;
    GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &GPIO_InitStruct);                                 // Apply config to port C for LORA module config

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource10, GPIO_AF_USART3);          // Activate alt function of pin 10 for UART
    GPIO_PinAFConfig(GPIOC, GPIO_PinSource11, GPIO_AF_USART3);          // Activate alt function of pin 11 for UART
    
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_4 | GPIO_Pin_5;                 // Reconfigure easy setup struct to target pins 4 and 5
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AN;                           // Reconfigure easy setup struct for analog mode
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_NOPULL;                       // Reconfigure easy setup struct for no pull
    GPIO_Init(GPIOC, &GPIO_InitStruct);                                 // Apply config to port C for water sensor pins (PC4 and PC5)

    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_4 | GPIO_Pin_5 | GPIO_Pin_6;    // Pin PA4 = CO, Pin PA5 = NH3, Pin PA6 = NO2 of the gas sensor
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AN;                           // Set to analog mode
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_NOPULL;                       // No pullup
    GPIO_Init(GPIOA, &GPIO_InitStruct);                                 // Apply config to port A to set up pins for ADC readings
}

/* Send a string char by char over USART3 until a null terminator is reached
*/
void USART_SendString(const char* str) {
    while (*str) {
        while (USART_GetFlagStatus(USART3, USART_FLAG_TXE) == RESET);
        USART_SendData(USART3, *str++);
    }
}

// Simple delay function using SysTick
void delay_ms(uint32_t ms) {
    uint32_t count = ms * (SystemCoreClock / 5000);  // Nominally running at 50MHz
    for (uint32_t i = 0; i < count; i++) {
        __NOP();  // No operation, consumes 1 cycle
    }
}

/* Send a string char by char over USART3 until a null terminator is reached,
   then append with "\r\n"
*/
void USART_SendStringWithNewLine(const char* str) {
  USART_SendString(str);
  USART_SendString("\r\n");
}

/* Send AT+ command to RYLR998 module using the above string sending functions
*/
void USART_SendATCommand(const char* comm) {
  USART_SendString("AT+");
  USART_SendStringWithNewLine(comm);
}

/* Configure ADC1 on Port A for reading from analogue gas sensor
*/
void configure_adc(void) {

    ADC_InitTypeDef ADC_InitStruct;
    ADC_InitStruct.ADC_Resolution = ADC_Resolution_12b;
    ADC_InitStruct.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStruct.ADC_ScanConvMode = ENABLE;  // Scan through channels
    ADC_InitStruct.ADC_ExternalTrigConvEdge = ADC_ExternalTrigConvEdge_None;
    ADC_InitStruct.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStruct.ADC_NbrOfConversion = NUM_READINGS;  // 3 channels

    ADC_Init(ADC1, &ADC_InitStruct);
    ADC_RegularChannelConfig(ADC1, ADC_Channel_4, 1, ADC_SampleTime_15Cycles);  // Channel 4 for CO 15cycles allows for a more stable reading (should be between 1-1000)
    ADC_RegularChannelConfig(ADC1, ADC_Channel_5, 2, ADC_SampleTime_15Cycles);  // Channel 5 for NH3 (should range from 1-300)
    ADC_RegularChannelConfig(ADC1, ADC_Channel_6, 3, ADC_SampleTime_15Cycles);  // Channel 6 for NO2 (should range from 0.05-10)
    ADC_Cmd(ADC1, ENABLE);                                                      // Enable ADC1
    ADC_EOCOnEachRegularChannelCmd(ADC1, ENABLE);                               // Enable EOC on ADC 1 flag for each channel conversion
    
    ADC_InitStruct.ADC_NbrOfConversion = (NUM_READINGS-1);                       // Reconfigur easy setup struct for 2 channels since we only have 2 water sensors
    ADC_Init(ADC2, &ADC_InitStruct);                                             // Apply easy config struct to ADC 2 to set up ADC for water sensors
    ADC_RegularChannelConfig(ADC2, ADC_Channel_14, 1, ADC_SampleTime_15Cycles);  // Channel 14 for TDS 15cycles allows for a more stable reading (should be between 1-1000)
    ADC_RegularChannelConfig(ADC2, ADC_Channel_15, 2, ADC_SampleTime_15Cycles);  // Channel 15 for TURB 15cycles allows for a more stable reading (should be between 1-1000)
    ADC_Cmd(ADC2 , ENABLE);                                                      // Enable ADC2
    ADC_EOCOnEachRegularChannelCmd(ADC2, ENABLE);                                // Enable EOC flag for each channel conversion




}

/* Configure USART3 on PC10 and PC11 for UART communication with RYLR998
*/
void configure_usart3(void) {
    USART_InitTypeDef USART_InitStruct;
    
    USART_InitStruct.USART_BaudRate = 115200;
    USART_InitStruct.USART_WordLength = USART_WordLength_8b;
    USART_InitStruct.USART_StopBits = USART_StopBits_1;
    USART_InitStruct.USART_Parity = USART_Parity_No;
    USART_InitStruct.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStruct.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART3, &USART_InitStruct);
    USART_Cmd(USART3, ENABLE);
}

uint16_t getResistance(channel_t channel) {
    unsigned long rs = 0;
    int counter = 0;

    switch (channel) {
        case CH_CO:      
            for(int i = 0; i < 100; i++) {
                rs += gas_readings[0];
                counter++;
                delay_ms(2);
            }
            return rs/counter;
        case CH_NH3:
            for(int i = 0; i < 100; i++) {
                rs += gas_readings[1];
                counter++;
                delay_ms(2);
            }
            return rs/counter;
        case CH_NO2:
            for(int i = 0; i < 100; i++) {
                rs += gas_readings[2];
                counter++;
                delay_ms(2);
            }
            return rs/counter;
    }

  return 0;
}



/* Read analogue data from ADC1 and convert to 16-bit unsigned integer
*/
void Read_Gas_ADC(void) {
    //Each sensor reading gives a RAW ADC conversion value between 0 and 4095 
    //Each reading is normalized to this scale and linearly transformed to match the 
    //Reading range that is compatible with the MICS6814 gas sensor for each gas concentration
    ADC_SoftwareStartConv(ADC1);
    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    gas_readings[0] = ADC_GetConversionValue(ADC1);             //Get RAW ADC CO reading
    ADC_ClearFlag(ADC1, ADC_FLAG_EOC);                            // Clear the EOC flag for the next channel

    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    gas_readings[1] = ADC_GetConversionValue(ADC1);             //Get RAW ADC NH3 reading
    ADC_ClearFlag(ADC1, ADC_FLAG_EOC);                            // Clear the EOC flag for the next channel

    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    gas_readings[2] = ADC_GetConversionValue(ADC1);             //Get RAW ADC NO2 reading
    ADC_ClearFlag(ADC1, ADC_FLAG_EOC);                            // Clear the EOC flag for the next channel
    
    return;

}

void Read_Water_ADC(void) {
    ADC_SoftwareStartConv(ADC2);
    while (ADC_GetFlagStatus(ADC2, ADC_FLAG_EOC) == RESET);
    water_readings[0] = ADC_GetConversionValue(ADC2);             //Get RAW ADC TDS reading
    ADC_ClearFlag(ADC2, ADC_FLAG_EOC);                            // Clear the EOC flag for the next channel

    while (ADC_GetFlagStatus(ADC2, ADC_FLAG_EOC) == RESET);
    water_readings[1] = ADC_GetConversionValue(ADC2);           //Get RAW ADC TURB reading
    ADC_ClearFlag(ADC2, ADC_FLAG_EOC);                            // Clear the EOC flag for the next channel

    return;
}

void calibrate_MICS() {
    // Continuously measure the resistance,
    // storing the last N measurements in a circular buffer.
    // Calculate the floating average of the last seconds.
    // If the current measurement is close to the average stop.

    // Allowed delta for the average from the current value
    uint8_t delta = 2;

    // Circular buffer for the measurements
    uint16_t bufferCO[SECONDS];
    uint16_t bufferNH3[SECONDS];
    uint16_t bufferNO2[SECONDS];
    // Pointers for the next element in the buffer
    // 32 because STM32 is 32-bit
    uint32_t pntrCO = 0;
    uint32_t pntrNH3 = 0;
    uint32_t pntrNO2 = 0;
    // Current floating sum in the buffer
    uint16_t fltSumCO = 0;
    uint16_t fltSumNH3 = 0;
    uint16_t fltSumNO2 = 0;

    // Current measurements;
    uint16_t curCO;
    uint16_t curNH3;
    uint16_t curNO2;

    // Flag to see if the channels are stable
    int CO_stable = 0;
    int NH3_stable = 0;
    int NO2_stable = 0;

    // Initialize buffer
    for (int i = 0; i < SECONDS; ++i) {
        bufferCO[i] = 0;
        bufferNH3[i] = 0;
        bufferNO2[i] = 0;
    }

    do {
        // Wait a second
        delay_ms(1000);
        // Read new resistances
        unsigned long rs = 0;
        delay_ms(50);
        for (int i = 0; i < 3; i++) {
            //Read new ADC data each time
            Read_Gas_ADC();
            delay_ms(1);
            rs += gas_readings[0];
        }
        curCO = rs/3;
        rs = 0;
        delay_ms(50);
        for (int i = 0; i < 3; i++) {
            Read_Gas_ADC();
            delay_ms(1);
            rs += gas_readings[1];
        }
        curNH3 = rs/3;
        rs = 0;
        delay_ms(50);
        for (int i = 0; i < 3; i++) {
            Read_Gas_ADC();
            delay_ms(1);
            rs += gas_readings[2];
        }
        curNO2 = rs/3;

        // Update floating sum by subtracting value
        // about to be overwritten and adding the new value.
        fltSumCO = fltSumCO + curCO - bufferCO[pntrCO];
        fltSumNH3 = fltSumNH3 + curNH3 - bufferNH3[pntrNH3];
        fltSumNO2 = fltSumNO2 + curNO2 - bufferNO2[pntrNO2];

        // Store new measurement in buffer
        bufferCO[pntrCO] = curCO;
        bufferNH3[pntrNH3] = curNH3;
        bufferNO2[pntrNO2] = curNO2;

        // Determine new state of flags
        CO_stable = (int) (abs(fltSumCO / SECONDS - curCO) < delta);
        NH3_stable = (int) (abs(fltSumNH3 / SECONDS - curNH3) < delta);
        NO2_stable = (int) (abs(fltSumNO2 / SECONDS - curNO2) < delta);

        // Advance buffer pointer
        pntrCO = (pntrCO + 1) % SECONDS ;
        pntrNH3 = (pntrNH3 + 1) % SECONDS;
        pntrNO2 = (pntrNO2 + 1) % SECONDS;

    } while (!CO_stable || !NH3_stable || !NO2_stable);

    CO_baseR = fltSumCO / SECONDS;
    NH3baseR = fltSumNH3 / SECONDS;
    NO2baseR = fltSumNO2 / SECONDS;

  // Store new base resistance values in EEPROM
}


uint16_t getBaseResistance(channel_t channel) {
    switch (channel) {
        case CH_CO:
            return CO_baseR;
        case CH_NH3:
            return NH3baseR;
        case CH_NO2:
            return NO2baseR;
    } 
    return 0;
}

float getCurrentRatio(channel_t channel) {
    float baseResistance = (float) getBaseResistance(channel);
    float resistance = (float) getResistance(channel);

    return resistance / baseResistance * ((float) (ADC_RANGE - 1) - baseResistance) / ((float) (ADC_RANGE - 1)  - resistance);
}

float measure_MICS(gas_t gas) {
    float ratio;
    float c = 0;

    switch (gas) {
        case CO:
            ratio = getCurrentRatio(CH_CO);
            c = pow(ratio, -1.179) * 4.385;
            break;
        case NH3:
            ratio = getCurrentRatio(CH_NH3);
            c = pow(ratio, -1.67) / 1.47;
            break;
        case NO2:
            ratio = getCurrentRatio(CH_NO2);
            c = pow(ratio, 1.007) / 6.855;
            break;
    }
    return isnan(c) ? -1 : c;
}

float get_TDS() {
    PC4_Voltage = (water_readings[0] / (float) ADC_RANGE) * 5.0;                 // Convert RAW ADC reading to a voltage
    ec_val = (133.42 * pow(PC4_Voltage, 3) - 255.86 * pow(PC4_Voltage, 2) + 857.39 * PC4_Voltage) * KVALUE;
    ec25_val = ec_val / (1.0 + 0.02 * (WATER_TEMPERATURE - 25.0));
    TDS_val = ec25_val * TDS_FACTOR;
    return TDS_val;
}

void Average_All_Data(){
    float sum = 0;
    for(int i = 0; i < DATA_POINTS_PER_HOUR; i++){ 
        sum = sum + CO_DataPoints[i];                               // Sum up all the data points taken over the last hour
    }
    Average_Hourly_CO = sum / ((float) DATA_POINTS_PER_HOUR);        // Divide the sum of all data points by the number of data points to update average
    sum = 0;                                                      // Reset the value of sum to 0 for next computation
    for(int i = 0; i < DATA_POINTS_PER_HOUR; i++){
        sum = sum + NH3_DataPoints[i];                              // Sum up all the data points taken over the last hour
    }
    Average_Hourly_NH3 = sum / ((float) DATA_POINTS_PER_HOUR);       // Divide the sum of all data points by the number of data points to update average
    sum = 0;                                                      // Reset the value of sum to 0 for next computation
    for(int i = 0; i < DATA_POINTS_PER_HOUR; i++){
        sum = sum + NO2_DataPoints[i];                              // Sum up all the data points taken over the last hour
      }
    Average_Hourly_NO2 = sum / ((float) DATA_POINTS_PER_HOUR);       // Divide the sum of all data points by the number of data points to update average
    sum = 0;                                                      // Reset the value of sum to 0 for next computation
    for(int i = 0; i < DATA_POINTS_PER_HOUR; i++){
        sum = sum + TDS_DataPoints[i];                              // Sum up all the data points taken over the last hour
    }
    Average_Hourly_TDS = sum / ((float) DATA_POINTS_PER_HOUR);       // Divide the sum of all data points by the number of data points to update average
}

int main() {
  
    __enable_irq();
    configure_rcc();
    configure_gpio();
    configure_adc();
    configure_usart3();

    // initialise band, network ID, and address of connected RYLR998 module
    USART_SendATCommand("BAND=915000000");
    delay_ms(500);
    USART_SendATCommand("NETWORKID=5");
    delay_ms(500);
    USART_SendATCommand("ADDRESS=1");
    delay_ms(500);
    
    USART_SendStringWithNewLine("Calibrating...");
    calibrate_MICS();
    
    char hourly_data[MAX_CHARS];
    char hn[MAX_CHARS];

    while (1) {
        if (samples_taken == DATA_POINTS_PER_HOUR){
            samples_taken = 0;                        //reset samples taken
            Average_All_Data();                       //compute hourly averages
            char hresp[MAX_CHARS] = "SEND=2,";        //send out hourly average data
            sprintf(hourly_data, "%s,%f,%f,%f,%f,%f,%f,turbidity_val_HOURLY", sensor_name, latitude, longitude, CO_val, NH3_val, NO2_val, TDS_val); 
            sprintf(hn, "%u", strlen(hourly_data));
            strcat(hresp, hn);
            strcat(hresp, ",");
            strcat(hresp, hourly_data);
            USART_SendATCommand(hresp);
        }

        Read_Gas_ADC();                                // Get new gas data 
        Read_Water_ADC();                              // Get new water data
        CO_val = measure_MICS(CO);                     // Update current CO val
        NH3_val = measure_MICS(NH3);                   // Update current NH3 val
        NO2_val = measure_MICS(NO2);                   // Update current NO2 val
        TDS_val = get_TDS();                           // Update current TDS val
        
        CO_DataPoints[samples_taken] = CO_val;
        NH3_DataPoints[samples_taken] = NH3_val;
        NO2_DataPoints[samples_taken] = NO2_val;
        TDS_DataPoints[samples_taken] = TDS_val;
        
        samples_taken++;                               // Update the number of samples taken this hour since system startup
        delay_ms(1000);                                // Short delay
    }
}