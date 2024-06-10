# StringTags: Smal library to handle some nice string formatting.
# Made by: Simon Kalmi Claesson
# Version: 1.2
#

# [Imports]
import socket
import re
import getpass

#                                     TAGNAMEs CAN ONLY CONTAIN `[A-Z][a-z][9-0]_-`
#
# Custom_Tags      {<tagName>}        PARSED FIRST AND GETS PRIO, SO THEY CAN CONTAIN TAGS.
#
# BuiltIn_Tags     {<tagName>}        PARSED SECONDLY.
#
# Placeholders     {<sym>} / §<sym>§  ONLY BUILTIN SYMBOLS:
#                                    "{esc}"=>"\033"  /  "§esc§"=>"\033"
#                                    "{\n}"=>"\n"     /  "§nl§"=>"\n"
#
# Unicode          {u.<unicode>}      ONLY UNICODE-CODEPOINTS IN CURRENT ENCODING
#
# Variable/Method  [<var/method>]     ONLY OBJS IN "allowedVariables" CAN USE SUBOBJS USING `.`
#                                    CALLS "Callables" AND RETURNS VALUE FOR THE REST.
#
# PaletteKeys      {p:<paletteKey>}   RETRIVES FORMATTING FROM "Palette"
#
# AnsiCode         {!<AnsiCode>}      FOR COLOR DON'T FORGET m AT THE END
#
# Hex Foreground   {#<hex6d>}         NO OPACITY SUPPORT
# Hex Background   {#!<hex6d>}        NO OPACITY SUPPORT
#
# RGB Foreground   {rgb.<R>;<G>;<B>}  INTEGER ONLY
# RGB Background   {rgb!<R>;<G>;<B>}  INTEGER ONLY
#
# Unformatted_Tags {^<tagName>}       WON'T BE FORMATTED SINCE LAST
#

# Main function