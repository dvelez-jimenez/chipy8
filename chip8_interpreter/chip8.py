
from typing import List
import random

class Chip8:

    fontset: bytearray = bytearray([
        0xF0, 0x90, 0x90, 0x90, 0xF0, # 0/ 0
        0x20, 0x60, 0x20, 0x20, 0x70, # 1/ 5
        0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2/ A
        0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3/ F
        0x90, 0x90, 0xF0, 0x10, 0x10, # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
        0xF0, 0x10, 0x20, 0x40, 0x40, # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90, # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
        0xF0, 0x80, 0x80, 0x80, 0xF0, # C
        0xE0, 0x90, 0x90, 0x90, 0xE0, # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F
    ])

    def initialize_optable(self):
        self.optable = {
            0x0000: self.opcode_group_0,
            0x1000: self.jump_to_address_nnn,
            0x2000: self.call_at_nnn,
            0x3000: self.skip_ins_vx_eq_nn,
            0x4000: self.skip_ins_vx_neq_nn,
            0x5000: self.skip_ins_vx_eq_vy,
            0x6000: self.set_vx_to_nn,
            0x7000: self.add_nn_to_vx,
            0x8000: self.opcode_group_8,
            0x9000: self.skip_ins_vx_neq_vy,
            0xA000: self.set_index_to_nnn,
            0xB000: self.jump_to_address_nnn_v0,
            0xC000: self.rnd_vx_nn,
            0xD000: self.draw_to_vram,
            0xE000: self.opcode_group_e,
            0xF000: self.opcode_group_f,
        }

    def __init__(self):
        self.opcode: int
        self.memory = bytearray([0x00] * 4096)

        # CPU Registers V0 - VF
        self.v: List[int] = [0] * 16

        # Index register
        self.i: int = 0x0
        # Program Counter
        self.pc: int = 0x200
        # 0x000-0x1FF - Chip 8 interpreter (contains font set in emu)
        # 0x050-0x0A0 - Used for the built in 4x5 pixel font set (0-F)
        # 0x200-0xFFF - Program ROM and work RAM

        # Screen is 64x32 pixels. Each pixel is one bit. but using a full int.
        self.vram: List[int] = [0] * (64*32)

        # 1 byte
        self.delay_timer: int = 0x0
        # 1 byte
        self.sound_timer: int = 0x0

        self.stack: List[int] = []
        self.sp: int = 0
        self.keyboard = {
            0x00: False,
            0x01: False,
            0x02: False,
            0x03: False,
            0x04: False,
            0x05: False,
            0x06: False,
            0x07: False,
            0x08: False,
            0x09: False,
            0x0A: False,
            0x0B: False,
            0x0C: False,
            0x0D: False,
            0x0E: False,
            0x0F: False,
        }

        self.paused = False
        self.timers_interval = 1/60
        self.last_ticks = 0
        self.draw_screen = False
        self.load_fontset()
        self.initialize_optable()
        self.debug = False

    def toggle_debug(self):
        self.debug = not self.debug

    def reset(self):
        self.opcode = 0
        self.v = [0] * 16
        self.i = 0x0
        self.pc: int = 0x200
        self.delay_timer = 0
        self.sound_timer = 0
        self.stack = []
        self.sp = 0
        self.paused = False
        self.load_fontset()
        self.last_ticks = 0

    def load_fontset(self):
        self.memory[0x00:len(Chip8.fontset)] = Chip8.fontset

    def load_program_to_memory(self, program: bytearray):
        self.memory[0x200:0x200+len(program)] = program

    def cycle(self, ticks):
        # Fetch
        self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc+1]
        if self.debug:
            print(f"Opcode: {self.opcode:04x}")
        # increment PC
        self.pc += 2

        # Decode
        # Get the function to execute from opcode table
        f = self.optable[self.opcode & 0xF000]
        """
            X: The second nibble. Used to look up one of the 16 registers (VX) from V0 through VF.
            Y: The third nibble. Also used to look up one of the 16 registers (VY) from V0 through VF.
            N: The fourth nibble. A 4-bit number.
            NN: The second byte (third and fourth nibbles). An 8-bit immediate number.
            NNN: The second, third and fourth nibbles. A 12-bit immediate memory address.
        """
        # Get the second nibble
        x = (self.opcode >> 8) & 0x0F
        # Get the third nibble
        y = (self.opcode >> 4) & 0x0F
        # Get the fourth nibble
        n = self.opcode & 0x000F
        # The second byte
        nn = self.opcode & 0x00FF
        # The second, third and fourth nibbles
        nnn = self.opcode & 0x0FFF

        # Execute
        f(x, y, n, nn, nnn)

        # Update Timers
        elapsed_ticks = ticks - self.last_ticks
        if elapsed_ticks > self.timers_interval:
            self.update_timers()
        self.last_ticks = ticks

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        
        if self.sound_timer > 0:
            self.sound_timer -= 1

    def nop(self, x, y, n, nn, nnn):
        if self.debug:
            print("NOPE!")
        return

    def opcode_group_0(self, x, y, n, nn, nnn):
        """
        0nnn - SYS addr
            Jump to a machine code routine at nnn.
            This instruction is only used on the old computers on which Chip-8 was originally implemented. It is ignored by modern interpreters.

        00E0 - CLS
            Clear the display.

        00EE - RET
            Return from a subroutine.
            The interpreter sets the program counter to the address at the top of the stack, then subtracts 1 from the stack pointer.
        
        0000 - HALT?
            Halts execution
        """
        if self.opcode == 0x0E0:
            if self.debug:
                print("Clearing the screen")
            # Clear the screen
            self.vram = [0] * (64 * 32)
            self.draw_screen = True
            return

        if self.opcode == 0x00EE:
            if self.debug:
                print("return from subroutine")
            self.pc = self.stack.pop()
            self.sp -= 1
            return
        
        if self.opcode == 0x000:
            self.pc -= 2
            return
        
        print(f"Unknow opcode: {self.opcode:04x}")

    def jump_to_address_nnn(self, x, y, n, nn, nnn):
        """
        1nnn - JP addr
            Jump to location nnn.
            The interpreter sets the program counter to nnn.
        """
        self.pc = nnn
        if self.debug:
            print(f"pc = {self.pc:04x}")
        return

    def call_at_nnn(self, x, y, n, nn, nnn):
        """
        2nnn - CALL addr
            Call subroutine at nnn.
            The interpreter increments the stack pointer, then puts the current PC on the top of the stack. The PC is then set to nnn.
        """
        self.sp += 1
        self.stack.append(self.pc)
        self.pc = nnn
        # // Stack size is 16 so we need to wrap
        return 

    def skip_ins_vx_eq_nn(self, x, y, n, nn, nnn):
        """
        3xkk : Skip next instruction if Vx = kk. 
            Compares register Vx to nn, and if they are equal, increments the program counter by 2
        """
        if self.v[x] == nn:
            self.pc += 2
        return

    def skip_ins_vx_neq_nn(self, x, y, n, nn, nnn):
        """
        4xkk : Skip next instruction if Vx != kk. 
            Compares register Vx to nn, and if they not are equal, increments the program counter by 2
        """
        if not self.v[x] == nn:
            self.pc += 2
        return

    def skip_ins_vx_eq_vy(self, x, y, n, nn, nnn):
        """
        5xy0: Skip next instruction if Vx = Vy. 
            compares register Vx to register Vy, and if they are equal, increments the program counter by 2.
        """
        if self.v[x] == self.v[y]:
            self.pc += 2
        return
    
    def set_vx_to_nn(self, x, y, n, nn, nnn):
        """
        6xkk - LD Vx, byte
            Set Vx = kk.
            The interpreter puts the value kk into register Vx.
        """
        # Only one opcode in 6, Sets VX to NN.
        # set register VX

        self.v[x] = nn
        if self.debug:
            print(f"v[{x}] = {self.v[x]:04x}")
        return

    def add_nn_to_vx(self, x, y, n, nn, nnn):
        """
        7xkk - ADD Vx, byte
            Set Vx = Vx + kk.
            Adds the value kk to the value of register Vx, then stores the result in Vx. 
        """
        # Only one opcode, Adds NN to VX. (Carry flag is not changed) 
        # add value to register VX.
        # Anding with 0xFF to ensure that only one byte is store. the overflow is thrown. (carry flag is not changed)
        self.v[x] = (self.v[x] + nn) & 0xFF
        if self.debug:
            print(f"v[{x}] = {self.v[x]:04x}")
        return

    def opcode_group_8(self, x, y, n, nn, nnn):
        """
        8xy0 - LD Vx, Vy
            Set Vx = Vy.
            Stores the value of register Vy in register Vx.
        
        8xy1 - OR Vx, Vy
            Set Vx = Vx OR Vy.
            Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx. 
        
        8xy2 - AND Vx, Vy
            Set Vx = Vx AND Vy.
            Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx. 
        
        8xy3 - XOR Vx, Vy
            Set Vx = Vx XOR Vy.
            Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx.
        
        8xy4 - ADD Vx, Vy
            Set Vx = Vx + Vy, set VF = carry.
            The values of Vx and Vy are added together. 
            If the result is greater than 8 bits (i.e., > 255,) VF is set to 1, 
            otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.
        
        8xy5 - SUB Vx, Vy
            Set Vx = Vx - Vy, set VF = NOT borrow. 
            If Vx > Vy, then VF is set to 1, otherwise 0. 
            Then Vy is subtracted from Vx, and the results stored in Vx.

        8xy6 - SHR Vx {, Vy}
            Set Vx = Vx SHR 1.
            If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. 
            Then Vx is divided by 2.

        8xy7 - SUBN Vx, Vy
            Set Vx = Vy - Vx, set VF = NOT borrow.
            If Vy > Vx, then VF is set to 1, otherwise 0. 
            Then Vx is subtracted from Vy, and the results stored in Vx.

        8xyE - SHL Vx {, Vy}
            Set Vx = Vx SHL 1.
            If the most-significant bit of Vx is 1, then VF is set to 1, 
            otherwise to 0. Then Vx is multiplied by 2.
        """
        if n == 0x0:
            self.v[x] = self.v[y]
        elif n == 0x1:
            self.v[x] |= self.v[y]
        elif n == 0x2:
            self.v[x] &= self.v[y]
        elif n == 0x3:
            self.v[x] ^= self.v[y]
        elif n == 0x4:
            sum = self.v[x] + self.v[y]
            self.v[x] = sum & 0xFF
            if sum > 0xFF:
                self.v[0xF] = 1
            else:
                self.v[0xF] = 0
        elif n == 0x5:
            xval = self.v[x]
            yval = self.v[y]
            if xval > yval:
                self.v[0xF] = 1
            else:
                self.v[0xF] = 0
            self.v[x] = (self.v[x] - self.v[y]) & 0xFF
        elif n == 0x6:
            #quirk
            # self.v[x] = self.v[y]
            self.v[0xF] = self.v[x] & 0x1
            self.v[x] = (self.v[x] >> 1) & 0xFF
        elif n == 0x7:
            xval = self.v[x]
            yval = self.v[y]
            if yval > xval:
                self.v[0xF] = 1
            else:
                self.v[0xF] = 0
            self.v[x] = (self.v[y] - self.v[x]) & 0xFF
        elif n == 0xE:
            #quirk
            # self.v[x] = self.v[y]
            self.v[0xF] = self.v[x] >> 7
            self.v[x] = (self.v[x] << 1) & 0xFF
        else:
            print(f"Unknow opcode: {self.opcode:04x}")


    def skip_ins_vx_neq_vy(self, x, y, n, nn, nnn):
        """
            9xy0: Skip next instruction if Vx != Vy. 
            compares register Vx to register Vy, and if they are not equal, increments the program counter by 2.
        """
        if not self.v[x] == self.v[y]:
            self.pc += 2  
        return

    def set_index_to_nnn(self, x, y, n, nn, nnn):
        """
        Annn - LD I, addr
            Set I = nnn.
            The value of register I is set to nnn.
        """
        # Only one opcode in A, Sets I to the address NNN. 
        # set index register I
        self.i = nnn
        if self.debug:
            print(f"I = {self.i:04x}")
        return

    def jump_to_address_nnn_v0(self, x, y, n, nn, nnn):
        """ 
        Bnnn - JP V0, addr
            Jump to location nnn + V0.
            The program counter is set to nnn plus the value of V0.
            Quirky instruction...
            Starting with CHIP-48 and SUPER-CHIP, it was changed to work as BXNN: 
            It will jump to the address XNN, plus the value in the register VX. 
            So the instruction B220 will jump to address 220 plus the value in the register V2.
        """
        self.pc = nnn + self.v[0]
        if self.debug:
            print(f"pc = {self.pc:04x}")
        return

    def rnd_vx_nn(self, x, y, n, nn, nnn):
        """ 
        Cxkk - RND Vx, byte
            Set Vx = random byte AND kk.
            The interpreter generates a random number from 0 to 255, 
            which is then ANDed with the value kk. 
            The results are stored in Vx. 
            See instruction 8xy2 for more information on AND.
        """
        self.v[x] = int(random.random()*255) & nn
        return

    def draw_to_vram(self, x, y, n, nn, nnn):
        """
        Dxyn - DRW Vx, Vy, nibble
            Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
        """
        if self.debug:
            print(f"DRAW! DXYN x:{x:02x}, y:{y:02x}, n:{n:02x}") 
        """ Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels and a height of N+1 pixels. 
            Each row of 8 pixels is read as bit-coded starting from memory location I; 
            I value doesn’t change after the execution of this instruction. 
            As described above, VF is set to 1 if any screen pixels are flipped from set to unset when the sprite is drawn, 
            and to 0 if that doesn’t happen 
        """
        self.v[0xF] = 0
        sprite_x_pos = self.v[x]
        sprite_y_pos = self.v[y]

        for y_offset in range(n):
            # Get the sprite line from memory
            sprite_line = self.memory[self.i + y_offset]
            for x_offset in range(8):
                pixel_index = ((sprite_x_pos+x_offset)%64) + (((sprite_y_pos+y_offset)%32)*64)
                pixel_value = sprite_line & (0x080 >> x_offset)
                # XOR
                if pixel_value:
                    if self.vram[pixel_index]:
                        self.v[0xF] = 1 
                    self.vram[pixel_index] ^= 0xFFFFFF
                    
        
        self.draw_screen = True
        return

    def opcode_group_e(self, x, y, n, nn, nnn):
        """
            Ex9E - SKP Vx
                Skip next instruction if key with the value of Vx is pressed.
                Checks the keyboard, and if the key corresponding to the value of Vx is currently in the down position, PC is increased by 2.
            ExA1 - SKNP Vx
                Skip next instruction if key with the value of Vx is not pressed.
                Checks the keyboard, and if the key corresponding to the value of Vx is currently in the up position, PC is increased by 2.
        """
        key = self.v[x]
        if nn == 0x9E:
            if self.keyboard[key]:
                self.pc += 2
        if nn == 0xA1:
            if not self.keyboard[key]:
                self.pc += 2
        else:
            print(f"Unknow opcode: {self.opcode:04x}")

    def opcode_group_f(self, x, y, n, nn, nnn):
        """ 
            FX07 sets VX to the current value of the delay timer
            FX15 sets the delay timer to the value in VX
            FX18 sets the sound timer to the value in VX
            FX1E: Add to index
                The index register I will get the value in VX added to it.
            FX0A: Get key
            FX29: Font character
                Fx29 - LD F, Vx
                Set I = location of sprite for digit Vx.
                The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx
            Fx33 - LD B, Vx
                Store BCD representation of Vx in memory locations I, I+1, and I+2.
                The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2.
        """
        if nn == 0x07:
            self.v[x] = self.delay_timer
        elif nn == 0x15:
            self.delay_timer = self.v[x]
        elif nn == 0x18:
            self.sound_timer = self.v[x]
        elif nn == 0x1E:
            self.i = self.i + self.v[x]
        elif nn == 0x0A:
            self.pc -= 2
            for key in self.keyboard.keys():
                if self.keyboard[key]:
                    self.v[x] = key
                    self.pc += 2
        elif nn == 0x29:
            self.i = self.v[x] * 0x5
        elif nn == 0x33:
            self.memory[self.i] = int((self.v[x]) / 100)
            self.memory[self.i+1] = int(((self.v[x]) / 10) % 10)
            self.memory[self.i+2] = int((self.v[x] % 100) % 10)
        elif nn == 0x55:
            addr = self.i
            for index in range(x+1):
                self.memory[addr] = self.v[index]
                addr += 1
        elif nn == 0x65:
            addr = self.i
            for index in range(x+1):
                self.v[index] = self.memory[addr]
                addr += 1
        else:
            print(f"Unknow opcode: {self.opcode:04x}")
        return

    def dump_memory(self):
        Chip8._dump_mem(self.memory)

    def dump_vram(self):
        Chip8._dump_mem(self.vram)

    def draw_vram(self):
        for y in range(32):
            for x in range(64):
                pixel_index = x + (y*64)
                pixel_value = "██" if self.vram[pixel_index] else "  "
                print(f"{pixel_value}", end='')
            print('')
        self.draw_screen = False



    @staticmethod
    def _dump_mem(mem):
        print(f"Offset(h)  00  01  02  03  04  05  06  07  08  09  0A  0B  0C  0D  0E  0F")
        for offset in range(len(mem)):
            if(offset%16 == 0):
                print(f"{offset:09x}  ", end= '')
            if((offset+1)%16 == 0):
                end = '\n'
            else:
                end = ''
            print(f"{mem[offset]:02x}  ", end=end)

    def print_registers(self):
        print(f" PC    I    V0  V1  V2  V3  V4  V5  V6  V7  V8  V9  VA  VB  VC  VD  VE  VF")
        print(f"{self.pc:04x}  {self.i:04x}  {self.v[0]:02x}  {self.v[1]:02x}  {self.v[2]:02x}  {self.v[3]:02x}  {self.v[4]:02x}  " +
              f"{self.v[5]:02x}  {self.v[6]:02x}  {self.v[7]:02x}  {self.v[8]:02x}  {self.v[9]:02x}  {self.v[10]:02x}  {self.v[11]:02x}  " +
              f"{self.v[12]:02x}  {self.v[13]:02x}  {self.v[14]:02x}  {self.v[15]:02x}")

