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

#ifdef CONFIG_BOARD_ESP32_WROOM_32
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_ESP32_WROOM_32 */

#ifdef CONFIG_BOARD_ESP8266_ESP_12X
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   4
#endif /* CONFIG_BOARD_ESP8266_ESP_12X */

#ifdef CONFIG_BOARD_NUCLEO_L476RG
#define F_CPU                   MHZ(80)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_NUCLEO_L476RG */

#ifdef CONFIG_BOARD_NUCLEO_F070RB
#define F_CPU                   MHZ(48)
#define INSTRUCTIONS_PER_SPIN   7
#endif /* CONFIG_BOARD_NUCLEO_F070RB */

#ifdef CONFIG_BOARD_SLSTK3402A
#define F_CPU                   MHZ(40)
#define INSTRUCTIONS_PER_SPIN   5
#endif /* CONFIG_BOARD_SLSTK3402A */