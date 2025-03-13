import array
import random
from time import sleep


#fmt: off
FONTS = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
]
# fmt: on

class Emulator:
    def __init__(self):
        self.memory = bytearray(4096)
        self.memory[0x50:0x9F] = FONTS

        self.registers = bytearray(16)
        self.stack = array.array("H", [0] * 16)  # 16-bit stack (unsigned short)
        
        self.index_register = 0
        self.program_counter = 0x200
        self.stack_pointer = 0

        self.delay_time = 0
        self.sound_time = 0

    def load_rom(self, file_path: str) -> None:
        with open(file_path, "rb") as file:
            self.memory[0x200:] = file.read()

    def run(self) -> None:
        while True:
            self.step()
            sleep(1 / 60)
    
    def step(self) -> None:
        """
        Execute the next instruction in memory.

        Each instruction is 2 bytes long and is stored in big-endian format.
        The following variables are used in the instructions:
        
        1. nnn or addr - A 12-bit value, the lowest 12 bits of the instruction
        2. n or nibble - A 4-bit value, the lowest 4 bits of the instruction
        3. x - A 4-bit value, the lower 4 bits of the high byte of the instruction
        4. y - A 4-bit value, the upper 4 bits of the low byte of the instruction
        5. kk or byte - An 8-bit value, the lowest 8 bits of the instruction
        """
        # All instructions are 2 bytes long, most-significant byte first
        b1, b2 = self.memory[self.program_counter : self.program_counter + 1]
        self.program_counter += 2

        # Split into 4-bit nibbles for easier processing
        n1 = b1 >> 4
        n2 = b1 & 0xF
        n3 = b2 >> 4
        n4 = b2 & 0xF

        # Execute instruction. See http://devernay.free.fr/hacks/chip8/C8TECH10.HTM
        match(n1, n2, n3, n4):
            case (0, 0, 0xE, 0):
                # Clear the screen
                ...
            case (0, 0, 0xE, 0xE):
                # Return from subroutine - set program counter to the address at the top of the stack
                self.program_counter = self.stack[self.stack_pointer]
                self.stack_pointer -= 1
            case (1, _, _, _):
                # Jump to address nnn
                self.program_counter = (n2 << 8 | b2)
            case (2, _, _, _):
                # Call subroutine at nnn - put counter on stack, then jump to nnn
                self.stack_pointer += 1
                self.stack[self.stack_pointer] = self.program_counter
                self.program_counter = n2 << 8 | b2
            case (3, _, _, _):
                # Skip next instruction if Vx == kk
                if self.registers[n2] == b2:
                    self.program_counter
            case (4, _, _, _):
                # Skip next instruction if Vx != kk
                if self.registers[n2] != b2:
                    self.program_counter += 2
            case (5, _, _, 0):
                # Skip next instruction if Vx == Vy
                if self.registers[n2] == self.registers[n3]:
                    self.program_counter += 2
            case (6, _, _, _):
                # Set Vx = kk
                self.registers[n2] = b2
            case (7, _, _, _):
                # Set Vx = Vx + kk
                self.registers[n2] = (self.registers[n2] + b2) & 0xFF
            case (8, _, _, 0):
                # Set Vx = Vy
                self.registers[n2] = self.registers[n3]
            case (8, _, _, 1):
                # Set Vx = Vx OR Vy
                self.registers[n2] |= self.registers[n3]
            case (8, _, _, 2):
                # Set Vx = Vx AND Vy
                self.registers[n2] &= self.registers[n3]
            case (8, _, _, 3):
                # Set Vx = Vx XOR Vy
                self.registers[n2] ^= self.registers[n3]
            case (8, _, _, 4):
                # Set Vx = Vx + Vy, set VF = carry
                self.registers[0xF] = 1 if self.registers[n2] + self.registers[n3] > 255 else 0
                self.registers[n2] = (self.registers[n2] + self.registers[n3]) & 0xFF
            case (8, _, _, 5):
                # Set Vx = Vx - Vy, set VF = NOT borrow
                self.registers[0xF] = 1 if self.registers[n2] > self.registers[n3] else 0
                self.registers[n2] = (self.registers[n2] - self.registers[n3]) & 0xFF
            case (8, _, _, 6):
                # Set Vx = Vx SHR 1 - VF set to least significant bit, then Vx /= 2
                self.registers[0xF] = self.registers[n2] & 1
                self.registers[n2] = self.registers[n2] >> 1
            case (8, _, _, 7):
                # Set Vx = Vy - Vx, set VF = NOT borrow
                self.registers[0xF] = 1 if self.registers[n3] > self.registers[n2] else 0
                self.registers[n2] = (self.registers[n3] - self.registers[n2]) & 0xFF
            case (8, _, _, 0xE):
                # Set Vx = Vx SHL 1 - VF set to most significant bit, then Vx *= 2
                self.registers[0xF] = (self.registers[n2] & 0x80) >> 7
                self.registers[n2] = (self.registers[n2] << 1) & 0xFF
            case (9, _, _, 0):
                # Skip next instruction if Vx != Vy
                if self.registers[n2] != self.registers[n3]:
                    self.program_counter += 2
            case (0xA, _, _, _):
                # Set I = nnn
                self.index_register = n2 << 8 | b2
            case (0xB, _, _, _):
                # Jump to location nnn + V0
                self.program_counter = self.registers[0] + (n2 << 8 | b2)
            case (0xC, _, _, _):
                # Set Vx = random byte AND kk
                self.registers[n2] = random.randint(0, 255) & b2
            case (0xD, _, _, _):
                # Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision
                # Sprites are XORed onto the existing screen -- if any pixels are erased, VF is set to 1, else 0
                # Display wraps around the screen if the sprite exceeds the screen dimensions
                ...
            case (0xE, _, 9, 0xE):
                # Skip next instruction if key with the value of Vx is pressed
                key = ...
                if key == self.registers[n2]:
                    self.program_counter += 2
            case (0xE, _, 0xA, 1):
                # Skip next instruction if key with the value of Vx is not pressed
                key = ...
                if key != self.registers[n2]:
                    self.program_counter += 2
            case (0xF, _, 0, 7):
                # Set Vx = delay timer value
                self.registers[n2] = self.delay_timer
            case (0xF, _, 0, 0xA):
                # Wait for a key press, store the value of the key in Vx
                key = ...
                self.registers[n2] = key
            case (0xF, _, 1, 5):
                # Set delay timer = Vx
                self.delay_timer = self.registers[n2]
            case (0xF, _, 1, 8):
                # Set sound timer = Vx
                self.sound_timer = self.registers[n2]
            case (0xF, _, 1, 0xE):
                # Set I = I + Vx
                index_register += self.registers[n2]
            case (0xF, _, 2, 9):
                # Set I = location of sprite for digit Vx
                ...
            case (0xF, _, 3, 3):
                # Store BCD representation of Vx in memory locations I, I+1, and I+2
                self.memory[self.index_register] = self.registers[n2] // 100  # Hundreds digit
                self.memory[self.index_register + 1] = (self.registers[n2] // 10) % 10  # Tens digit
                self.memory[self.index_register + 2] = self.registers[n2] % 10  # Ones digit
            case (0xF, _, 5, 5):
                # Store registers V0 through Vx into memory starting at location I
                self.memory[self.index_register : self.index_register + n2 + 1] = self.registers[:n2 + 1]
            case (0xF, _, 6, 5):
                # Read into registers V0 through Vx from memory starting at location I
                self.registers[:n2 + 1] = self.memory[self.index_register : self.index_register + n2 + 1]
            case _:
                raise NotImplementedError("Unknown instruction")
