#include "stm32f4xx.h"
#include "stm32f4xx_usart.h"
#include "stm32f4xx_gpio.h"
#include "stm32f4xx_adc.h"
#include "stm32f4xx_rcc.h"
#include "stm32f4_discovery.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

// Max ADC resolution is 4096 (12-bit)
#define MAX_DIGITS 4

/* Configure clocks for USART3 (DO NOT use USART1, it has a capacitor which
   garbles the output), Port C, Port B, and ADC1.
*/
void configure_rcc(void) {
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);      // Init USART3 clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOC, ENABLE);       // Init GPIOC clock
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOB, ENABLE);       // Init GPIOB clock
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1, ENABLE);        // init ADC1 clock
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
    
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_1;                      // Pin PB1, connect to either CO, NH3, or NO2 of the gas sensor
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AN;                   // Set to analog mode
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_NOPULL;
    GPIO_Init(GPIOB, &GPIO_InitStruct);                         // Apply config to port B
}

/* Configure ADC1 on PB1 for reading from analogue gas sensor
*/
void configure_adc(void) {
    ADC_InitTypeDef ADC_InitStruct;
    
    ADC_InitStruct.ADC_Resolution = ADC_Resolution_12b;
    ADC_InitStruct.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStruct.ADC_ScanConvMode = DISABLE;
    ADC_InitStruct.ADC_ExternalTrigConvEdge = ADC_ExternalTrigConvEdge_None;
    ADC_InitStruct.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStruct.ADC_NbrOfConversion = 1;  
    
    ADC_Init(ADC1, &ADC_InitStruct);                            // Apply ADC config to ADC1

    ADC_Cmd(ADC1, ENABLE);                                      // Enable ADC1
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

/* Read analogue data from ADC1 and convert to 16-bit unsigned integer
*/
uint16_t Read_ADC(void) {
    ADC_SoftwareStartConv(ADC1);
    while (ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC) == RESET);
    return ADC_GetConversionValue(ADC1);
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

// Simple delay function using SysTick
// NOT ENTIRELY ACCURATE, MUST UPDATE
void delay_ms(uint32_t ms) {
    for (uint32_t i = 0; i < ms * 20000; i++) {
        __NOP(); // No operation, just a waste cycle
    }
}

int main() {
    configure_rcc();
    configure_gpio();
    configure_adc();
    configure_usart3();
    
    SysTick_Config(SystemCoreClock / 1000);

    // initialise band, network ID, and address of connected RYLR998 module
    USART_SendATCommand("BAND=915000000");
    delay_ms(500);
    USART_SendATCommand("NETWORKID=5");
    delay_ms(500);
    USART_SendATCommand("ADDRESS=1");
    delay_ms(500);
    
    char str[MAX_DIGITS];
    char n;
    
    uint16_t analogue_val;

    while (1) {
        // other RYLR998 module has address 2, also of the same band and net ID
        char resp[50] = "SEND=2,";
        analogue_val = Read_ADC();
        sprintf(str, "%u", (uint16_t) analogue_val);
        sprintf(&n, "%u", strlen(str));
        strcat(resp, &n);
        strcat(resp, ",");
        strcat(resp, str);
        USART_SendATCommand(resp); // Transmit data
        delay_ms(5000);
    }
}