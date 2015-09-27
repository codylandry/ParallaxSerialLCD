
import serial
import time
import TextWrap


class LCD(object):
    """
    A class for communicating with the 2x16 LCD Display:
    Parallax Inc. 27977 Serial LCD with speaker
    """
    def __init__(self, _port="/dev/ttyAMA0",_baudrate=9600):
        self.ser = serial.Serial(port=_port, baudrate=_baudrate)
        self.NEXTLINE = chr(13)
        self.CLEARSCREEN = chr(12)
        self.BACKLIGHT_ON = chr(17)
        self.BACKLIGHT_OFF = chr(18)
        self.DISPLAY_OFF = chr(21)
        self.LEFT = chr(8)
        self.RIGHT = chr(9)
        self.PAUSE = chr(232)
        self.BLANK_LINE = " " * 16
        self.NOTE_LIST = [r"A",  r"A#", "B",  "C",  # List of notes in order
                          r"C#", "D",  r"D#", "E",
                          r"F",  r"F#", "G",  r"G#"]
        self.OCTAVE_LIST = ["3rd", "4th", "5th", "6th", "7th"]   # List of octaves in order
        self.NOTE = {r"A": chr(220),  r"A#": chr(221), r"B": chr(222),  r"C": chr(223),
                     r"C#": chr(224), r"D": chr(225),  r"D#": chr(226), r"E": chr(227),
                     r"F": chr(228),  r"F#": chr(229), r"G": chr(230),  r"G#": chr(231)}
        
        self.NOTE_LENGTH = {"1/32": (chr(209), .0625),         # .0625 Seconds
                            "1/16": (chr(210), .125),          # .125 Seconds
                            "1/8": (chr(211), .25),            # .25 Seconds
                            "1/4": (chr(212), .5),             # .5 Seconds
                            "1/2": (chr(213), 1),              # 1 Second
                            "1": (chr(214), 2)}                # 2 Second
        
        self.OCTAVE = {"3rd": chr(215),          # 220Hz
                       "4th": chr(216),          # 440Hz
                       "5th": chr(217),          # 880Hz
                       "6th": chr(218),          # 1760Hz
                       "7th": chr(219)}          # 3520Hz
        self.text = ["", ""]                     # keeps track of displayed text on lines 0 and 1
        self.pos = [0, 0]                        # line, pos 0-15
        self.mode = 1                            # Flag for mode for cursor and blinking, default to 1
        self.backlight_status = False            # Flag for the status of the backlight
        self.clear()

    def set_display_off(self):
        self.ser.write(self.DISPLAY_OFF)

    def set_backlight_on(self):
        self.ser.write(self.BACKLIGHT_ON)
        self.backlight_status = True

    def set_backlight_off(self):
        self.ser.write(self.BACKLIGHT_OFF)
        self.backlight_status = False

    def set_display_on(self, mode=1):
        if mode == 1:
            message = chr(24)       # Default mode, cursor on and no blink
        elif mode == 2:
            message = chr(25)       # cursor on and character blink
        elif mode == 3:
            message = chr(22)       # cursor off and no blink
        elif mode == 4:
            message = chr(23)       # cursor off and character blink
        else:
            raise ValueError("mode must be an int from 1-4")
        self.ser.write(message)

    def set_mode(self, mode=None):
        if mode:
            self.mode = mode
        self.set_display_off()
        self.set_display_on(self.mode)

    def text_update(self, line0 = None, line1=None):
        """
        Adds trailing spaces and keeps track of what's actually on the display.
        """
        filler = " "
        if line0 is None:
            line0 = self.text[0]
        if line1 is None:
            line1 = self.text[1]
        line0_actual = line0
        line1_actual = line1
        line0_spaces = 16 - len(line0)
        line1_spaces = 16 - len(line1)
        for c in range(0, line0_spaces):
            line0_actual += filler
        for c in range(0, line1_spaces):
            line1_actual += filler
        self.text[0] = line0_actual
        self.text[1] = line1_actual

    def next_line(self):
        """next_line()
        moves cursor to the next line 0-1, 1-0"""
        if self.pos[0] == 0:
            self.pos = [1, 0]
        else:
            self.pos = [0, 0]
        self.ser.write(self.NEXTLINE)

    def clear(self):
        """clear()
        sends command to clear the display and move the cursor to pos 0,0"""
        self.ser.write(self.CLEARSCREEN)
        time.sleep(.005)
        self.text_update("", "")

    def write_text(self, line0=None, line1=None):
        """write_text(line0 : string, line1 : string)
        Write text to the display.  Only update the lines you want.
        If you want to display more 16 chars, only use line0."""
        if line1:
            if len(line1) > 16:
                raise ValueError
        if line0 is None:
            line0 = self.text[0]
        if line1 is None:
            if self.text[1] == self.BLANK_LINE:
                if len(line0) > 16:
                    lines = TextWrap.wrap(line0, 16)
                    line0, line1 = lines
                else:
                    line1 = self.text[1]

        self.text_update(line0=line0, line1=line1)
        self.move_to_pos(0, 0)
        self.ser.write(self.text[0] + self.text[1])

    def flash_text(self, line0="", line1="", duration=2, revert=False, blink=None):
        """flash_text(line0 : string, line1 : string, duration : float)
        flashes the given text on the screen for the given duration in seconds.
        specify return as True if you want to automatically return to the original text."""

        timer = time.time() + duration

        if revert:
            original_text = list(self.text)
        self.clear()
        self.write_text(line0, line1)

        while time.time() < timer:
            if blink:
                self.set_backlight_off()
                time.sleep(blink)
                self.set_backlight_on()
                time.sleep(blink)
            else:
                pass
        self.clear()

        if revert:
            self.write_text(original_text[0], original_text[1])

    def scroll_text(self, text, speed, reformat=True):

        if reformat:
            text_list = TextWrap.wrap(text, 16)
        else:
            text_list = text
        for i in range(len(text_list)):
            if i < len(text_list) - 1:
                self.flash_text(text_list[i], text_list[i+1], speed)
            if i == len(text_list) - 1:
                self.flash_text(text_list[i], duration=speed)

    def move_to_pos(self, line, pos):
        line_0_positions = [chr(i) for i in range(128, 144)]
        line_1_positions = [chr(i) for i in range(148, 164)]
        if pos > 15 or pos < 0:
            raise ValueError
        if line == 0:
            self.ser.write(line_0_positions[pos])
            self.pos = [0,pos]
        elif line == 1:
            self.ser.write(line_1_positions[pos])
            self.pos = [1, pos]
        else:
            raise ValueError

    def set_notelength(self, length):
        self.ser.write(self.NOTE_LENGTH[length][0])

    def play_note(self, note, notelength = None):
        if notelength:
            self.ser.write(self.NOTE_LENGTH[notelength][0])
        self.ser.write(self.NOTE[note])

    def play_song(self, song):
        wait = .15
        for i in song:
            if i in self.NOTE.keys():
                self.play_note(i)
                time.sleep(wait)
            elif i in self.NOTE_LENGTH.keys():
                self.ser.write(self.NOTE_LENGTH[i][0])
                wait = self.NOTE_LENGTH[i][1] * 1.5
            else:
                raise KeyError("%s is not a note or notelength" % i)

        
if __name__ == "__main__":
    import time
    lcd = LCD()
    lcd.set_display_on()
    lcd.set_backlight_on()
    lcd.flash_text("Starting", "Demonstration", 2)
    lcd.flash_text("Example #1:", "Music")
    lcd.set_notelength("1/32")
    lcd.play_song(lcd.NOTE_LIST)
    end = time.time() + 5
    while time.time() < end:
        lcd.set_mode(3)
        timestring = [time.strftime("   %H:%M:%S", time.localtime()), time.strftime("%a, %d %b %Y", time.localtime())]
        lcd.write_text(timestring[0], timestring[1])
    lcd.flash_text("This is 'flash'", "text of 4 secs.", duration=4)
    lcd.play_note("A", "1/4")
    test_text = """This is a test of the scrolling function for a 2x16 display.
    This allows you to pass a long string of text and scroll the output to the
    user at a predefined speed in seconds."""
    lcd.scroll_text(test_text, 1.25)
    lcd.set_display_off()
    lcd.set_backlight_off()
