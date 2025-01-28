#include "stm32f4xx.h"
#include "stm32f4xx_usart.h"
#include "stm32f4_discovery.h"

void configure_rcc(void) {
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);
  RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
}

void configure_gpio(void) {
  GPIO_InitTypeDef GPIO_InitStruct;
  GPIO_InitStruct.GPIO_Pin = GPIO_Pin_9 | GPIO_Pin_10;
  GPIO_InitStruct.GPIO_Mode = GPIO_Mode_AF;
  GPIO_InitStruct.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStruct.GPIO_PuPd = GPIO_PuPd_UP;
  GPIO_InitStruct.GPIO_Speed = GPIO_Speed_50MHz;
  GPIO_Init(GPIOA, &GPIO_InitStruct);
  /* Connect USART pins to AF */
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource9, GPIO_AF_USART1); // USART1_TX
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource10, GPIO_AF_USART1); // USART1_RX
}

void USART_PutChar(uint8_t ch) {
    USART_SendData(USART1, (uint16_t) ch);
    while(USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET);
    USART_SendData(USART1, (uint16_t) ch);
}

void configure_usart1(void) {
  USART_InitTypeDef USART_InitStruct;
  
  USART_InitStruct.USART_BaudRate = 9600;
  USART_InitStruct.USART_WordLength = USART_WordLength_8b;
  USART_InitStruct.USART_StopBits = USART_StopBits_1;
  USART_InitStruct.USART_Parity = USART_Parity_No;
  USART_InitStruct.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
  USART_InitStruct.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
  USART_Init(USART1, &USART_InitStruct);
  USART_Cmd(USART1, ENABLE);
}
int main()
{
  //Enable the GPIOD Clock
  configure_rcc();
  configure_gpio();
  configure_usart1();
  
  while (1) {
    USART_PutChar(0x48);
    USART_PutChar(0x49);
    USART_PutChar(0x21);
  }
}
