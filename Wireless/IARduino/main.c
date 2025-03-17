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

#define ADC_RANGE               4096    // Max ADC resolution is 4096 (12-bit)
#define ADDRESS                 "1"
#define BAND                    "915000000"
#define BAUD_RATE               115200
#define CO_FACTOR               4.385
#define CO_POWER               -1.179
#define DATA_POINTS_PER_HOUR    5     // Current implementation takes new samples every ~5 seconds... 3600 seconds in an hour so 3600/5 = 720 samples per hour
#define EC_VAL_1ST_PWR_FACTOR   857.39
#define EC_VAL_2ND_PWR_FACTOR   255.86
#define EC_VAL_3RD_PWR_FACTOR   133.42
#define KVALUE                  1       // Assuming room temp water 25 deg C - more accurate readings can be made if we actually took water temps
#define LATITUDE                47.653132
#define LONGITUDE              -122.306114
#define MAX_CHARS               240     // Max length of char payload from RYLR998
#define MAX_DIGITS              4       // Number of ADC digits
#define NETWORK_ID              "5"
#define NH3_FACTOR              1.47
#define NH3_POWER              -1.67
#define NO2_FACTOR              6.855
#define NO2_POWER               1.007
#define NUM_GASES               3       // Number of gases
#define NUM_PERIPHERALS         5       // Total number of measurement peripherals
#define NUM_READINGS            3       // Number of readings to take from each gas
#define RESISTANCE_SAMPLES      100     // Number of samples to take for calculating base resistance
#define SECONDS                 5       // Number of seconds
#define SENSOR_NAME             "prototype"
#define TDS_FACTOR              0.5     // TDS factor
#define V_REF                   5       // Reference voltage (5V)
#define WATER_TEMPERATURE       25      // Water in degrees Celsius at room temperature

// Global variables to store current gas reading data (these may change after each ADC reading)
float ec25_val;
float ec_val;
float PC4_Voltage;

int samples_taken = 0;                                  // This keeps track of how many samples have been taken since system startup

uint16_t base_resistances[NUM_GASES];

float data_points[NUM_PERIPHERALS][DATA_POINTS_PER_HOUR];
float hourly_averages[NUM_PERIPHERALS];
float vals[NUM_PERIPHERALS];

uint16_t gas_readings[NUM_GASES];                       // Buffer of size 3 to hold CO, NH3, NO2 values
uint16_t water_readings[NUM_PERIPHERALS - NUM_GASES];   // Buffer of size 2 to hold TDS and TURB values

// Enum for proper peripheral declaration
enum peripheral {
  CO, NH3, NO2, TDS, TURB
};

typedef enum peripheral peripheral_t;

/* Configure clocks for USART3 (DO NOT use USART1, it has a capacitor which
   garbles the output), Port C, Port B, and ADC1.
*/
void configure_RCC(void) {
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);      // Init USART3 clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);       // Init GPIOC clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);       // Init GPIOB clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);       // Init GPIOA clock

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE);        // init ADC1 clock
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC2, ENABLE);        // init ADC2 clock
}

/* Configure GPIO pins 10 and 11 for Port C and pin 1 for Port B
*/
void configure_GPIO(void) {
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
void USART_send_string(const char* str) {
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
void USART_send_string_with_new_line(const char* str) {
    USART_send_string(str);
    USART_send_string("\r\n");
}

/* Send AT+ command to RYLR998 module using the above string sending functions
*/
void USART_send_AT_command(const char* comm) {
    USART_send_string("AT+");
    USART_send_string_with_new_line(comm);
}

/* Configure ADC1 on Port A for reading from analogue gas sensor
*/
void configure_ADC(void) {
    ADC_InitTypeDef ADC_InitStruct;
    ADC_InitStruct.ADC_Resolution = ADC_Resolution_12b;
    ADC_InitStruct.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStruct.ADC_ScanConvMode = ENABLE;
    ADC_InitStruct.ADC_ExternalTrigConvEdge = ADC_ExternalTrigConvEdge_None;
    ADC_InitStruct.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStruct.ADC_NbrOfConversion = NUM_READINGS;

    ADC_Init(ADC1, &ADC_InitStruct);
    ADC_RegularChannelConfig(ADC1, ADC_Channel_4, 1, ADC_SampleTime_15Cycles);  // Channel 4 for CO 15cycles allows for a more stable reading (should be between 1-1000)
    ADC_RegularChannelConfig(ADC1, ADC_Channel_5, 2, ADC_SampleTime_15Cycles);  // Channel 5 for NH3 (should range from 1-300)
    ADC_RegularChannelConfig(ADC1, ADC_Channel_6, 3, ADC_SampleTime_15Cycles);  // Channel 6 for NO2 (should range from 0.05-10)
    ADC_Cmd(ADC1, ENABLE);                                                      // Enable ADC1
    ADC_EOCOnEachRegularChannelCmd(ADC1, ENABLE);                               // Enable EOC on ADC 1 flag for each channel conversion
    
    ADC_InitStruct.ADC_NbrOfConversion = (NUM_READINGS - 1);                    // Reconfigure easy setup struct for 2 channels since we only have 2 water sensors
    ADC_Init(ADC2, &ADC_InitStruct);                                            // Apply easy config struct to ADC 2 to set up ADC for water sensors
    ADC_RegularChannelConfig(ADC2, ADC_Channel_14, 1, ADC_SampleTime_15Cycles); // Channel 14 for TDS 15cycles allows for a more stable reading (should be between 1-1000)
    ADC_RegularChannelConfig(ADC2, ADC_Channel_15, 2, ADC_SampleTime_15Cycles); // Channel 15 for TURB 15cycles allows for a more stable reading (should be between 1-1000)
    ADC_Cmd(ADC2 , ENABLE);                                                     // Enable ADC2
    ADC_EOCOnEachRegularChannelCmd(ADC2, ENABLE);                               // Enable EOC flag for each channel conversion
}

/* Configure USART3 on PC10 and PC11 for UART communication with RYLR998
*/
void configure_USART3(void) {
    USART_InitTypeDef USART_InitStruct;
    
    USART_InitStruct.USART_BaudRate = BAUD_RATE;
    USART_InitStruct.USART_WordLength = USART_WordLength_8b;
    USART_InitStruct.USART_StopBits = USART_StopBits_1;
    USART_InitStruct.USART_Parity = USART_Parity_No;
    USART_InitStruct.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStruct.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART3, &USART_InitStruct);
    USART_Cmd(USART3, ENABLE);
}

uint16_t get_resistance(peripheral_t p) {
    if (p > NO2) {
        return 0;
    }
    unsigned long rs = 0;
    
    for (int i = 0; i < RESISTANCE_SAMPLES; i++) {
         rs += gas_readings[p];
         delay_ms(2);
    }

    return (uint16_t) (rs / RESISTANCE_SAMPLES);
}

/* Read analogue data from ADC1 and convert to 16-bit unsigned integer
*/
void read_gas_ADC(void) {
    //Each sensor reading gives a RAW ADC conversion value between 0 and 4095 
    //Each reading is normalized to this scale and linearly transformed to match the 
    //Reading range that is compatible with the MICS6814 gas sensor for each gas concentration
    ADC_SoftwareStartConv(ADC1);
    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    gas_readings[CO] = ADC_GetConversionValue(ADC1);            // Get RAW ADC CO reading
    ADC_ClearFlag(ADC1, ADC_FLAG_EOC);                          // Clear the EOC flag for the next channel

    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    gas_readings[NH3] = ADC_GetConversionValue(ADC1);           // Get RAW ADC NH3 reading
    ADC_ClearFlag(ADC1, ADC_FLAG_EOC);                          // Clear the EOC flag for the next channel

    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    gas_readings[NO2] = ADC_GetConversionValue(ADC1);           // Get RAW ADC NO2 reading
    ADC_ClearFlag(ADC1, ADC_FLAG_EOC);                          // Clear the EOC flag for the next channel
}

void read_water_ADC(void) {
    ADC_SoftwareStartConv(ADC2);
    
    while (ADC_GetFlagStatus(ADC2, ADC_FLAG_EOC) == RESET);
    water_readings[TDS - NUM_GASES] = ADC_GetConversionValue(ADC2);     // Get RAW ADC TDS reading
    ADC_ClearFlag(ADC2, ADC_FLAG_EOC);                                  // Clear the EOC flag for the next channel

    while (ADC_GetFlagStatus(ADC2, ADC_FLAG_EOC) == RESET);
    water_readings[TURB - NUM_GASES] = ADC_GetConversionValue(ADC2);    // Get RAW ADC TURB reading
    ADC_ClearFlag(ADC2, ADC_FLAG_EOC);                                  // Clear the EOC flag for the next channel
}

uint16_t calibrate_resistance(peripheral_t p) {
    if (p > NO2) {
        return 0;
    }
    
    unsigned long rs = 0;
    
    for (int i = 0; i < NUM_READINGS; i++) {
        read_gas_ADC();                                                 // Read new ADC data each time
        delay_ms(1);
        rs += gas_readings[p];
    }
    
    return (uint16_t) (rs / NUM_READINGS);
}

void calibrate_MICS() {
    // Continuously measure the resistance,
    // storing the last N measurements in a circular buffer.
    // Calculate the floating average of the last seconds.
    // If the current measurement is close to the average stop.

    // Allowed delta for the average from the current value
    uint8_t delta = 2;

    // Circular buffer for the measurements
    uint16_t buffers[NUM_GASES][SECONDS];
    
    // Array of pointers for the aforementioned measurement buffer
    uint32_t pntr_arr[NUM_GASES] = {0, 0, 0};
    
    // Floating sums for each of the gases
    uint16_t floating_sums[NUM_GASES] = {0, 0, 0};
    
    // Current measurements for each of the gases
    uint16_t current_measurements[NUM_GASES];
    
    // Stability flags for each of the gases
    int stable[NUM_GASES] = {0, 0, 0};

    // Initialize buffers
    for (peripheral_t p = CO; p < TDS; p++) {
        for (int i = 0; i < SECONDS; i++) {
            buffers[p][i] = 0;
        }
    }

    do {
        // Wait a second
        delay_ms(1000);
        
        // Read new resistances
        for (peripheral_t p = CO; p < TDS; p++) {
            current_measurements[p] = calibrate_resistance(p);
            delay_ms(50);
        }
        
        // Update floating sum by subtracting value
        // about to be overwritten and adding the new value.
        for (peripheral_t p = CO; p < TDS; p++) {
            floating_sums[p] += current_measurements[p] - buffers[p][pntr_arr[p]];
            buffers[p][pntr_arr[p]] = current_measurements[p];
            stable[p] = (int) (abs(floating_sums[p] / SECONDS - current_measurements[p]) < delta);
            pntr_arr[p] = (pntr_arr[p] + 1) % SECONDS;
        }

    } while (!stable[CO] || !stable[NH3] || !stable[NO2]);
    
    for (peripheral_t p = CO; p < TDS; p++) {
        base_resistances[p] = floating_sums[p] / SECONDS;
    }
}

float get_current_ratio(peripheral_t p) {
    if (p > NO2) {
        return (float) 0.0;
    }
    
    float base_resistance = (float) base_resistances[p];
    float resistance = (float) get_resistance(p);

    return resistance / base_resistance * ((float) (ADC_RANGE - 1) - base_resistance) / ((float) (ADC_RANGE - 1)  - resistance);
}

float measure_MICS(peripheral_t p) {
    float ratio;
    float c = 0.0;

    switch (p) {
        case CO:
            ratio = get_current_ratio(CO);
            c = pow(ratio, CO_POWER) * CO_FACTOR;
            break;
        case NH3:
            ratio = get_current_ratio(NH3);
            c = pow(ratio, NH3_POWER) / NH3_FACTOR;
            break;
        case NO2:
            ratio = get_current_ratio(NO2);
            c = pow(ratio, NO2_POWER) / NO2_FACTOR;
            break;
        default:
            c = 0.0;
    }
    
    return isnan(c) ? -1.0 : c;
}

float get_TDS() {
    PC4_Voltage = (water_readings[TDS - NUM_GASES] / (float) ADC_RANGE) * (float) V_REF;                 // Convert RAW ADC reading to a voltage
    ec_val = (EC_VAL_3RD_PWR_FACTOR * pow(PC4_Voltage, 3)
            - EC_VAL_2ND_PWR_FACTOR * pow(PC4_Voltage, 2)
            + EC_VAL_1ST_PWR_FACTOR * PC4_Voltage) * KVALUE;
    ec25_val = ec_val / (1.0 + 0.02 * (WATER_TEMPERATURE - 25.0));
    return ec25_val * TDS_FACTOR;
}

float get_TURB() {
    return water_readings[TURB - NUM_GASES] * ((float) V_REF / (float) ADC_RANGE);
}

void average_all_data(){
    for (peripheral_t p = CO; p <= TURB; p++) {
        float sum = 0;
        for (int s = 0; s < DATA_POINTS_PER_HOUR; s++) {
            sum += data_points[p][s];
        }
        hourly_averages[p] = sum / ((float) DATA_POINTS_PER_HOUR);
    }
}

int main() {
    __enable_irq();
    configure_RCC();
    configure_GPIO();
    configure_ADC();
    configure_USART3();

    // initialise band, network ID, and address of connected RYLR998 module
    char band[MAX_CHARS] = "BAND=";
    strcat(band, BAND);
    USART_send_AT_command(band);
    delay_ms(500);
    
    char network_id[MAX_CHARS] = "NETWORKID=";
    strcat(network_id, NETWORK_ID);
    USART_send_AT_command(network_id);
    delay_ms(500);
    
    char address[MAX_CHARS] = "ADDRESS=";
    strcat(address, ADDRESS);
    USART_send_AT_command(address);
    delay_ms(500);
    
    calibrate_MICS();
    
    char hourly_data[MAX_CHARS];
    char hn[MAX_CHARS];

    while (1) {
        if (samples_taken == DATA_POINTS_PER_HOUR){
            samples_taken = 0;                        //reset samples taken
            average_all_data();                       //compute hourly averages
            char hresp[MAX_CHARS] = "SEND=2,";        //send out hourly average data
            sprintf(hourly_data, "%s,%f,%f,%f,%f,%f,%f,%f", SENSOR_NAME, LATITUDE, LONGITUDE, hourly_averages[CO], hourly_averages[NH3], hourly_averages[NO2], hourly_averages[TDS], hourly_averages[TURB]); 
            sprintf(hn, "%u", strlen(hourly_data));
            strcat(hresp, hn);
            strcat(hresp, ",");
            strcat(hresp, hourly_data);
            USART_send_AT_command(hresp);
        }

        read_gas_ADC();                                // Get new gas data 
        read_water_ADC();                              // Get new water data
        
        for (peripheral_t p = CO; p < TDS; p++) {
            vals[p] = measure_MICS(p);
        }
        vals[TDS] = get_TDS();                         // Update current TDS val
        vals[TURB] = get_TURB();
        
        for (peripheral_t p = CO; p <= TURB; p++) {
            data_points[p][samples_taken] = vals[p];
        }
        
        samples_taken++;                               // Update the number of samples taken this hour since system startup
        delay_ms(1000);                                // Short delay
    }
}
