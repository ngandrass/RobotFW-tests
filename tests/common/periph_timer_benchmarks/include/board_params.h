/*
 * Copyright (C) 2021 HAW Hamburg - Niels Gandraß
 *
 * This file is subject to the terms and conditions of the GNU Lesser
 * General Public License v2.1. See the file LICENSE in the top level
 * directory for more details.
 */

/**
 * @ingroup tests
 * @{
 *
 * @file        board_params.h
 * @brief       Board specific configuration params for periph_utimer benchmarks
 *
 * @author      Niels Gandraß <niels@gandrass.de>
 *
 * @}
 */

#ifdef CONFIG_BOARD_ARDUINO_MEGA2560
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(16)
#define INSTRUCTIONS_PER_SPIN   7
#endif /* CONFIG_BOARD_ARDUINO_MEGA2560 */

#ifdef CONFIG_BOARD_ESP32_WROOM_32
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_ESP32_WROOM_32 */

#ifdef CONFIG_BOARD_ESP8266_ESP_12X
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   4
#endif /* CONFIG_BOARD_ESP8266_ESP_12X */

#ifdef CONFIG_BOARD_NUCLEO_F070RB
#define F_CPU                   MHZ(48)
#define INSTRUCTIONS_PER_SPIN   7
#endif /* CONFIG_BOARD_NUCLEO_F070RB */

#ifdef CONFIG_BOARD_NUCLEO_F103RB
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(72)
#define INSTRUCTIONS_PER_SPIN   8
#endif /* CONFIG_BOARD_NUCLEO_F103RB */

#ifdef CONFIG_BOARD_NUCLEO_F767ZI
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(216)
#define INSTRUCTIONS_PER_SPIN   2
#endif /* CONFIG_BOARD_NUCLEO_F767ZI */

#ifdef CONFIG_BOARD_NUCLEO_G474RE
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(170)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_NUCLEO_G474RE */

#ifdef CONFIG_BOARD_NUCLE0_L152RE
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(32)
#define INSTRUCTIONS_PER_SPIN   (6 * 0.9995)
#endif /* CONFIG_BOARD_NUCLEO_L152RE */

#ifdef CONFIG_BOARD_NUCLEO_L476RG
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_NUCLEO_L476RG */

#ifdef CONFIG_BOARD_SLSTK3400A
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(24)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_SLSTK3400A */

#ifdef CONFIG_BOARD_SLSTK3401A
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(40)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_SLSTK3401A */

#ifdef CONFIG_BOARD_SLSTK3402A
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(40)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_SLSTK3402A */

#ifdef CONFIG_BOARD_STK3200
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(24)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_STK3200 */

#ifdef CONFIG_BOARD_Z1
#ifndef F_CPU
#define F_CPU                   CLOCK_CORECLOCK  // MHZ(8)
#endif
#define INSTRUCTIONS_PER_SPIN   (7 * 1.0275)
#endif /* CONFIG_BOARD_Z1 */
