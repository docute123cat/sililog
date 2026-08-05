---
# ⚠️ FILE NÀY DO sync.py SINH RA — MỌI SỬA ĐỔI SẼ BỊ MẤT.
# Sửa bản gốc tại: 50 - Blog/getting-uart-to-print-on-stm32.md
title: "Getting UART to Print on STM32 Without HAL"
date: 2026-08-02
tags: ["stm32", "bare-metal", "uart", "debugging"]
summary: "A peripheral needs two clocks enabled, not one."
repo: "https://github.com/docute123cat/stm32-bare-metal"
draft: false
categories: ["embedded", "bare-metal"]
---
## What I was trying to do
Send "hello" over UART2 on an STM32F4 Discovery, no HAL, registers only.

## What went wrong
Nothing on the serial monitor. Code compiled and ran fine.

## How I debugged it
Logic analyzer on PA2 — the line was flat. So the pin was never
actually driven by the UART peripheral.

## The bug
I enabled the USART2 clock but forgot the **GPIOA** clock, and never set
the alternate function. The pin stayed a plain input.

```c
RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;   // this line was missing
GPIOA->MODER |= (2 << (2 * 2));        // PA2 -> alternate function
GPIOA->AFR[0] |= (7 << (4 * 2));       // AF7 = USART2
```

## What I learned
On STM32, a peripheral needs **two** clocks enabled: the peripheral's own
and the GPIO port's. Reading the datasheet's clock tree earlier would
have saved me two hours.
