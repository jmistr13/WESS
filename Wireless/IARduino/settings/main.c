#include "stm32f4xx.h"
#include "stm32f4xx_usart.h"
#include "stm32f4xx_gpio.h"
#include "stm32f4_discovery.h"
#include <string.h>

#define MAX_BUFFER_SIZE 240

char uart_buffer[MAX_BUFFER_SIZE];
uint8_t buffer_index = 0;

void configure_rcc(void) {
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
    RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOD, ENABLE);
}

void configure_gpio(void) {
    GPIO_InitTypeDef GPIO_InitStruct;
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_9 | GPIO_Pin_10;
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AF;
    GPIO_InitStruct.GPIO_OType = GPIO_OType_PP;
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_UP;
    GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_PinAFConfig(GPIOA, GPIO_PinSource9, GPIO_AF_USART1);  // TX
    GPIO_PinAFConfig(GPIOA, GPIO_PinSource10, GPIO_AF_USART1); // RX
    
    GPIO_InitStruct.GPIO_Pin = GPIO_Pin_12 | GPIO_Pin_14;
    GPIO_InitStruct.GPIO_Mode = GPIO_Mode_OUT;
    GPIO_InitStruct.GPIO_OType = GPIO_OType_PP;
    GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_NOPULL;
    GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOD, &GPIO_InitStruct);
}

void USART_SendString(const char* str) {
    while (*str) {
        while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);  // Wait until TX buffer is empty
        USART_SendData(USART1, *str++);
    }

    // Ensure both '\r' and '\n' are sent properly
    while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    USART_SendData(USART1, '\r');  // Carriage return

    while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    USART_SendData(USART1, '\n');  // Newline

    // Ensure data is fully sent before returning
    while (USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET);
}

void USART1_IRQHandler(void) {
    if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET) {
        char received = USART_ReceiveData(USART1);

        // Store in buffer if space allows
        if (buffer_index < MAX_BUFFER_SIZE - 1) {
            uart_buffer[buffer_index++] = received;
            uart_buffer[buffer_index] = '\0'; // Null-terminate
        }
    }
}

void configure_usart1(void) {
    USART_InitTypeDef USART_InitStruct;
    
    USART_InitStruct.USART_BaudRate = 115200;
    USART_InitStruct.USART_WordLength = USART_WordLength_8b;
    USART_InitStruct.USART_StopBits = USART_StopBits_1;
    USART_InitStruct.USART_Parity = USART_Parity_No;
    USART_InitStruct.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStruct.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART1, &USART_InitStruct);
    USART_Cmd(USART1, ENABLE);
    
    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
    NVIC_EnableIRQ(USART1_IRQn);
}

// Simple delay function using SysTick
void delay_ms(uint32_t ms) {
    for (uint32_t i = 0; i < ms * 4000; i++) {
        __NOP(); // No operation, just a waste cycle
    }
}

void process_uart_response(void) {
    if (strstr(uart_buffer, "Hello")) {
        GPIO_SetBits(GPIOD, GPIO_Pin_12);  // Green LED ON
        delay_ms(5000);
        GPIO_ResetBits(GPIOD, GPIO_Pin_12); // Green LED OFF
    } 
    else /* if (strstr(uart_buffer, "+ERR=1")) */ {
        GPIO_SetBits(GPIOD, GPIO_Pin_14);  // Red LED ON
        delay_ms(5000);
        GPIO_ResetBits(GPIOD, GPIO_Pin_14); // Red LED OFF
    }

    // Clear buffer
    buffer_index = 0;
    memset(uart_buffer, 0, MAX_BUFFER_SIZE);
}

int main() {
    configure_rcc();
    configure_gpio();
    configure_usart1();

    /* USART_SendString("AT+BAND=915000000");
    delay_ms(500);
    USART_SendString("AT+NETWORKID=5");
    delay_ms(500);
    USART_SendString("AT+ADDRESS=2");
    delay_ms(500); */

    while (1) {
        USART_SendString("Hello"); // Transmit data
        delay_ms(5000);

        // Seems like the UART parameters are not configured properly.
        // Supposed to loop back whatever is sent with PA9 and PA10 connected to each other.
        process_uart_response(); // Check response and blink LED
    }
}