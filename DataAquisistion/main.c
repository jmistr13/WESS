#include "stm32f4xx.h"
#include "stm32f4xx_usart.h"
#include "stm32f4xx_gpio.h"
#include "stm32f4xx_adc.h"
#include "stm32f4xx_rcc.h"
#include "stm32f4xx_dma.h"
#include "stm32f4_discovery.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

//Global variables to store current gas reading data (these may change after each ADC reading)
uint16_t CO_val;
uint16_t NH3_val;
uint16_t NO2_val;

// Max ADC resolution is 4096 (12-bit)
#define MAX_DIGITS 4
#define NUM_READINGS 3
#define MAX_CHARS 240

uint16_t readings[NUM_READINGS];

/* Configure clocks for USART3 (DO NOT use USART1, it has a capacitor which
   garbles the output), Port C, Port B, and ADC1.
*/
void configure_rcc(void) {
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);      // Init USART3 clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);       // Init GPIOC clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);       // Init GPIOB clock
    
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);       // Init GPIOA clock

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE);        // init ADC1 clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_DMA2, ENABLE);
}

/* Configure GPIO pins 10 and 11 for Port C and pin 1 for Port B
*/
void configure_gpio(void) {
    GPIO_InitTypeDef GPIO_InitStruct;
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_10 | GPIO_Pin_11;       // Pin PC10, connect to RX of RYLR998
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AF;                   // Pin PC11, connect to TX of RYLR998
    GPIO_InitStruct.GPIO_OType = GPIO_OType_PP;
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_UP;
    GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOC, &GPIO_InitStruct);                         // Apply config to port C

    GPIO_PinAFConfig(GPIOC, GPIO_PinSource10, GPIO_AF_USART3);
    GPIO_PinAFConfig(GPIOC, GPIO_PinSource11, GPIO_AF_USART3);
    
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_4 | GPIO_Pin_5 | GPIO_Pin_6;                      // Pin PA4 = CO, Pin PA5 = NH3, Pin PA6 = NO2 of the gas sensor
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AN;                                             // Set to analog mode
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_NOPULL;
    GPIO_Init(GPIOA, &GPIO_InitStruct);                                                   // Apply config to port A to set up pins for ADC readings
}

/* Send a string char by char over USART3 until a null terminator is reached
*/
void USART_SendString(const char* str) {
    while (*str) {
        while (USART_GetFlagStatus(USART3, USART_FLAG_TXE) == RESET);
        USART_SendData(USART3, *str++);
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
    /*
    ADC_CommonInitTypeDef ADC_CommonInitStruct;
    ADC_CommonInitStruct.ADC_DMAAccessMode = ADC_DMAAccessMode_1;
    ADC_CommonInitStruct.ADC_Mode = ADC_Mode_Independent;
    ADC_CommonInitStruct.ADC_TwoSamplingDelay = ADC_TwoSamplingDelay_5Cycles;
    ADC_CommonInitStruct.ADC_Prescaler = ADC_Prescaler_Div2;
    ADC_CommonInit(&ADC_CommonInitStruct);
    */

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

    ADC_Cmd(ADC1, ENABLE); // Enable ADC1
    ADC_EOCOnEachRegularChannelCmd(ADC1, ENABLE);               // Enable EOC flag for each channel conversion

    //ADC_SoftwareStartConv(ADC1); // Start conversion manually
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
/*
void configure_dma(void) {
    DMA_InitTypeDef DMA_InitStruct;
    DMA_InitStruct.DMA_Channel = DMA_Channel_0;  // ADC1 uses DMA2, stream 0, channel 0
    DMA_InitStruct.DMA_PeripheralBaseAddr = (uint32_t)&ADC1->DR;  // ADC1 data register
    DMA_InitStruct.DMA_Memory0BaseAddr = (uint32_t)&readings;  // Destination buffer
    DMA_InitStruct.DMA_DIR = DMA_DIR_PeripheralToMemory;  // Transfer from ADC to memory
    DMA_InitStruct.DMA_BufferSize = NUM_READINGS;  // Number of items to transfer (3 channels)
    DMA_InitStruct.DMA_PeripheralInc = DMA_PeripheralInc_Disable;
    DMA_InitStruct.DMA_MemoryInc = DMA_MemoryInc_Enable;  // Enable memory increment for storing in `readings[]`
    DMA_InitStruct.DMA_PeripheralDataSize = DMA_PeripheralDataSize_HalfWord;  // 16-bit data
    DMA_InitStruct.DMA_MemoryDataSize = DMA_MemoryDataSize_HalfWord;
    DMA_InitStruct.DMA_Mode = DMA_Mode_Circular;  // Circular mode for continuous transfers
    DMA_InitStruct.DMA_Priority = DMA_Priority_High;
    DMA_InitStruct.DMA_FIFOMode = DMA_FIFOMode_Disable;
    DMA_InitStruct.DMA_FIFOThreshold = DMA_FIFOThreshold_Full;
    DMA_InitStruct.DMA_MemoryBurst = DMA_MemoryBurst_Single;
    DMA_InitStruct.DMA_PeripheralBurst = DMA_PeripheralBurst_Single;

    DMA_Init(DMA2_Stream0, &DMA_InitStruct);  // Initialize DMA
    DMA_Cmd(DMA2_Stream0, ENABLE);  // Enable DMA stream
    
    // Enable ADC DMA after ADC is properly configured
    ADC_DMACmd(ADC1, ENABLE);  // Enable ADC DMA
    NVIC_EnableIRQ(DMA2_Stream0_IRQn);  // Enable interrupt for DMA
    NVIC_SetPriority(DMA2_Stream0_IRQn, 0);  // Ensure interrupt priority is correct
}

void DMA2_Stream0_IRQHandler(void) {
    if (DMA_GetITStatus(DMA2_Stream0, DMA_IT_TCIF0)) { // Check if DMA transfer completed
        if (DMA_GetFlagStatus(DMA2_Stream0, DMA_FLAG_TCIF0)) {
            // DMA transfer complete, debug message
            USART_SendStringWithNewLine("DMA Transfer Complete");

            // Print the readings for debugging
            char str[MAX_CHARS];
            sprintf(str, "CO: %u, NH3: %u, NO2: %u", readings[0], readings[1], readings[2]);
            USART_SendStringWithNewLine(str);

            // Clear the DMA interrupt flag
            DMA_ClearITPendingBit(DMA2_Stream0, DMA_IT_TCIF0);
        }
    }
}
*/


/* Read analogue data from ADC1 and convert to 16-bit unsigned integer
*/
void Read_ADC(void) {
    //Each sensor reading gives a RAW ADC conversion value between 0 and 4095 
    //Each reading is normalized to this scale and linearly transformed to match the 
    //Reading range that is compatible with the MICS6814 gas sensor for each gas concentration
    ADC_SoftwareStartConv(ADC1);
    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    readings[0] = /* (uint16_t) ( */ ADC_GetConversionValue(ADC1)/*/4095)*999 + (1-52.9626)*/;             //Get CO, normalize, and recalibrate
    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    readings[1] = /* (uint16_t) ( */ ADC_GetConversionValue(ADC1)/*/4095)*299 + (1-9.25079)*/;             //Get NH3, normalize, and recalibrate
    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    readings[2] = /* (uint16_t) ( */ ADC_GetConversionValue(ADC1)/*/4095)*(10-0.05)+(0.05-6.02919)*/;      //Get NO2, normalize, and recalibrate
    return;

    //return ADC_GetConversionValue(ADC1);
}

// Simple delay function using SysTick
// NOT ENTIRELY ACCURATE, MUST UPDATE
void delay_ms(uint32_t ms) {
    for (uint32_t i = 0; i < ms * 20000; i++) {
        __NOP(); // No operation, just a waste cycle
    }
}

int main() {
  
    __enable_irq();
    
    configure_rcc();
    configure_gpio();
    configure_adc();
    configure_usart3();
    //configure_dma();
    
    SysTick_Config(SystemCoreClock / 1000);

    // initialise band, network ID, and address of connected RYLR998 module
    USART_SendATCommand("BAND=915000000");
    delay_ms(500);
    USART_SendATCommand("NETWORKID=5");
    delay_ms(500);
    USART_SendATCommand("ADDRESS=1");
    delay_ms(500);
    
    char str[MAX_CHARS];
    char n[MAX_CHARS];

    while (1) {
        // other RYLR998 module has address 2, also of the same band and net ID
        char resp[MAX_CHARS] = "SEND=2,";
        Read_ADC();
        CO_val =  (uint16_t) ((readings[0] / 4095.0) * 999.0 + (1-52.9626));
        NH3_val = (uint16_t) ((readings[1] / 4095.0) * 299.0 + (1-9.25079));
        NO2_val = (uint16_t) ((readings[2] / 4095.0) * (10-0.05) + (0.05-6.02919));
        
        sprintf(str, "CO: %u, NH3: %u, NO2: %u", CO_val, NH3_val, NO2_val);
        sprintf(n, "%u", strlen(str));
        strcat(resp, n);
        strcat(resp, ",");
        strcat(resp, str);
        USART_SendATCommand(resp); // Transmit data
        DMA_ClearFlag(DMA2_Stream0, DMA_FLAG_TCIF0);
        delay_ms(5000);
    }
}