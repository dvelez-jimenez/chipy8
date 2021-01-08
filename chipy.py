import random
import os
import pygame
from pygame import constants as pygamec

from chip8_interpreter.chip8 import Chip8

WIDTH = 640
HEIGHT = 480
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ChipPy Python CHIP8 Emulator")


# 123C
# 456D
# 789E
# A0BF
KEYMAP = {
    pygamec.K_1: 0x01, pygamec.K_2: 0x02, pygamec.K_3: 0x03, pygamec.K_4: 0x0C,
    pygamec.K_q: 0x04, pygamec.K_w: 0x05, pygamec.K_e: 0x06, pygamec.K_r: 0x0D,
    pygamec.K_a: 0x07, pygamec.K_s: 0x08, pygamec.K_d: 0x09, pygamec.K_f: 0x0E,
    pygamec.K_z: 0x0A, pygamec.K_x: 0x00, pygamec.K_c: 0x0B, pygamec.K_v: 0x0F
}

def main():
    # Initialize interpreter
    mychip8 = Chip8()

    #Load program from file
    #with open("roms/ibmlogo.ch8", "rb") as in_file:
    #    rom_data = in_file.read()

    #with open("roms/test_opcode.ch8", "rb") as in_file:
    #    rom_data = in_file.read()

    #with open("roms/bx_test.ch8", "rb") as in_file:
    #    rom_data = in_file.read()
    
    #with open("roms/brixch8.ch8", "rb") as in_file:
    #    rom_data = in_file.read()

    #with open("roms/delay_timer_test.ch8", "rb") as in_file:
    #    rom_data = in_file.read()

    #with open("roms/keypad_test.ch8", "rb") as in_file:
    #    rom_data = in_file.read()

    #with open("roms/trip8.ch8", "rb") as in_file:
    #    rom_data = in_file.read()

    with open("roms/octojam2title.ch8", "rb") as in_file:
        rom_data = in_file.read()



    if rom_data:
        mychip8.load_program_to_memory(rom_data)
    else:
        raise Exception("Could not load rom")

    #Set up pygame
    run = True
    run_chip8 = False
    cycle_chip8 = False
    FPS = 480
    clock = pygame.time.Clock()
    chip8_screen = pygame.Surface((64, 32))

    def redraw_window(draw_chip8_screen: bool = False):
        if draw_chip8_screen:
            pygame.transform.scale(chip8_screen, (WIDTH, HEIGHT), WINDOW)
            #WINDOW.blit(chip8_screen, (0,0))
        pygame.display.update()

    def draw_vram_to_surface(target_surface, vram: bytearray):
        width = target_surface.get_width()
        height = target_surface.get_height()
        if not len(vram) ==  (width*height):
            raise Exception(f"surface must be same size as vram, surface len(): {width*height}, vram len(), {len(vram)}")

        with pygame.PixelArray(target_surface) as pixel_array:
            for y in range(height):
                for x in range(width):
                    pixel_array[x][y] = vram[x + (y*width)]
    

    bg = WINDOW.get_rect()
    pygame.draw.rect(WINDOW, 255, bg)


    while run:
        ticks = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygamec.QUIT:
                run = False
            elif event.type == pygamec.KEYDOWN:
                if event.key == pygamec.K_p:
                    print("stopping emulator...")
                    run_chip8 = False
                if event.key == pygamec.K_u:
                    print("running emulator...")
                    run_chip8 = True
                if event.key == pygamec.K_SPACE:
                    cycle_chip8 = True
                if event.key == pygamec.K_k:
                    run = False
                if event.key == pygamec.K_l:
                    mychip8.draw_vram()
                    mychip8.dump_memory()
                if event.key == pygamec.K_j:
                    mychip8.toggle_debug()
        
        pressed_keys = pygame.key.get_pressed()
        for key in KEYMAP.keys():
            if pressed_keys[key]:
                mychip8.keyboard[KEYMAP[key]] = True
            else:
                mychip8.keyboard[KEYMAP[key]] = False
        
        #if mychip8.sound_timer > 0:
        #    print("beep")
            
        if run_chip8 or cycle_chip8:
            mychip8.cycle(ticks)
            cycle_chip8 = False
            if mychip8.debug:
                mychip8.print_registers()
        
        if mychip8.draw_screen:
            draw_vram_to_surface(chip8_screen, mychip8.vram)
        
        redraw_window(mychip8.draw_screen)


# Run Main
main()
