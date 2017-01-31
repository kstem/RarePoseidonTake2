"""
Module for playing games of Go using GoTextProtocol

This code is based off of the gtp module in the Deep-Go project
by Isaac Henrion and Aamos Storkey at the University of Edinburgh.
"""
import traceback
import sys
import os
from board import GoBoard
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, FLOODFILL
import numpy as np
import re

class GtpConnection():

    def __init__(self, go_engine,outfile = '/tmp/gtp_log', debug_mode = True):
        """
        object that plays Go using GTP

        Parameters
        ----------
        go_engine : GoPlayer
            a program that is capable of playing go by reading GTP commands
        komi : float
            komi used for the current game
        board: GoBoard
            SIZExSIZE array representing the current board state
        """
        mode='w'
        self.stdout = sys.stdout
        #sys.stdout = outfile
        self._debug_mode = debug_mode
        self.file = open(outfile, mode)
        #self.stderr = sys.stderr
        sys.stdout = self
        self.go_engine = go_engine
        self.komi = 0
        self.board = GoBoard(3) #TODO: chang default siz back to 7
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "set_free_handicap": self.set_free_handicap,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "final_score": self.final_score_cmd,
            "legal_moves": self.legal_moves_cmd
        }

        # used for argument checking
        # values: (required number or arguments, error message on argnum failure)
        self.argmap = {
            "boardsize": (1, 'Usage: boardsize INT'),
            "komi": (1, 'Usage: komi FLOAT'),
            "known_command": (1, 'Usage: known_command CMD_NAME'),
            "set_free_handicap": (1, 'Usage: set_free_handicap MOVE (e.g. A4)'),
            "genmove": (1, 'Usage: genmove {w,b}'),
            #"play": (2, 'Usage: play {b,w} MOVE'),
            "play": (2, ' wrong number of arguments'),
            
            "legal_moves": (1, 'Usage: legal_moves {w,b}')
        }
    
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data) 

    def flush(self,):
        self.stdout.flush()
        self.file.flush()

    def start_connection(self):
        """
        start a GTP connection. This function is what continuously monitors the user's
        input of commands.
        """
        self.debug_msg("Start up successful...\n\n")
        line = sys.stdin.readline()
        while line:
            self.get_cmd(line)
            line = sys.stdin.readline()

    def get_cmd(self, command):
        """
        parse the command and execute it

        Arguments
        ---------
        command : str
            the raw command to parse/execute
        """
        if len(command.strip(' \r\t')) == 0:
            return
        if command[0] == '#':
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]; args = elements[1:]
        if self.arg_error(command_name, len(args)):
           # print(' ', args, " wrong number of arguments")
            player_errors(2, None, None, args)
            sys.stdout.flush()
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error('Unknown command')
            sys.stdout.flush()

    def arg_error(self, cmd, argnum):
        """
        checker funciton for the number of arguments given to a command

        Arguments
        ---------
        cmd : str
            the command name
        argnum : int
            number of parsed argument

        Returns
        -------
        True if there was an argument error
        False otherwise
        """
        if cmd in self.argmap and self.argmap[cmd][0] > argnum:
               # print("yoyoyo what up from the south side", self.argmap[cmd][1]) remove
                self.error(self.argmap[cmd][1])
                return True
        return False

    def debug_msg(self, msg=''):
        """ Write a msg to the debug stream """
        if self._debug_mode:
            sys.stderr.write(msg); sys.stderr.flush()

    def error(self, error_msg=''):
        """ Send error msg to stdout and through the GTP connection. """
        sys.stdout.write('illegal move')
       #original sys.stdout.write('illegal move: [input]  {}\n\n'.format(error_msg)); sys.stdout.flush()
       # sys.stdout.write('illegal move: '+elements[0]+' {}\n\n'.format(error_msg))

    def respond(self, response=''):
        """ Send msg to stdout """
  #      sys.stdout.write("worrrrrrrrdddddddddsssss")
        sys.stdout.write('= {}\n\n'.format(response)); sys.stdout.flush()

    def reset(self, size):
        """
        Resets the state of the GTP to a starting board

        Arguments
        ---------
        size : int
            the boardsize to reinitialize the state to
        """
        self.board.reset(size)

    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond('2')

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the player """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the player """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game and initialize with a new boardsize

        Arguments
        ---------
        args[0] : int
            size of reinitialized board
        """
        self.reset(int(args[0]))
        self.respond()

    def showboard_cmd(self, args):
        self.respond('\n' + str(self.board.get_twoD_board()))

    def komi_cmd(self, args):
        """
        Set the komi for the game

        Arguments
        ---------
        args[0] : float
            komi value
        """
        self.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if a command is known to the GTP interface

        Arguments
        ---------
        args[0] : str
            the command name to check for
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(' '.join(list(self.commands.keys())))

    def set_free_handicap(self, args):
        """
        clear the board and set free handicap for the game

        Arguments
        ---------
        args[0] : str
            the move to handicap (e.g. B2)
        """
        self.board.reset(self.board.size)
        for point in args:
            move = GoBoardUtil.move_to_coord(point, self.board.size)
            point = self.board._coord_to_point(*move)
            if not self.board.move(point, BLACK):
                print("if not self.board.move --- in set_free_handicap")
                self.debug_msg("Illegal Move: {}\nBoard:\n{}\n".format(move, str(self.board.get_twoD_board())))
        self.respond()

    def legal_moves_cmd(self, args):
        """
        list legal moves for the given color
        Arguments
        ---------
        args[0] : {'b','w'}
            the color to play the move as
            it gets converted to  Black --> 1 White --> 2
            color : {0,1}
            board_color : {'b','w'}
        """
        try:
            board_color = args[0].lower()
            color= GoBoardUtil.color_to_int(board_color)
            moves=GoBoardUtil.generate_legal_moves(self.board,color)
            self.respond(moves)
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

    def play_cmd(self, args):
        """
        play a move as the given color

        Arguments
        ---------
        args[0] : {'b','w'}
            the color to play the move as
            it gets converted to  Black --> 1 White --> 2
            color : {0,1}
            board_color : {'b','w'}
        args[1] : str
            the move to play (e.g. A5)
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]
           # self.respond("2") remove
            color= GoBoardUtil.color_to_int(board_color)
            print(color)
            if color == 9:
                self.respond('yo0000')
                self.respond(args[0])
                self.respond(args[1])
                #self.respond(color)
                print('illegal move: ', args[0])
                player_errors(3, 2, args[1], args) #TODO: here. '2' to try and force it to work 
            #TODO: hi need to fix the pass as pastsing isn't allowed - adam
            if args[1].lower()=='pass':
                self.debug_msg("Player {} is passing\n".format(args[0]))
                #self.respond()
                self.respond("game over, no passing allowed scrub")
                self.respond(self.board.final_score(self.komi))
                return
            move = GoBoardUtil.move_to_coord(args[1], self.board.size)
            if move:
                move = self.board._coord_to_point(move[0],move[1])
                print("Playing Move")
                print("ENTERING IF ALMOST")
                #if GoBoardUtil.generate_random_move(self.board, color) == None:
                #    print("IN THE FINAL GAME SHOULD BE OVER")
                #    self.final_score_cmd([])
            # move == None on pass
            else:
                self.error("Error in executing the move %s, check given move: %s"%(move,args[1]))
                return
            if not self.board.move(move, color):
                self.respond("Illegal Move: {}".format(board_move), msg)
                return
            else:
                self.debug_msg("Move: {}\nBoard:\n{}\n".format(board_move, str(self.board.get_twoD_board())))
            print("ENTERING IF ALMOST")
            if GoBoardUtil.generate_random_move(self.board, GoBoardUtil.opponent(color)) == None:
                print("IN THE FINAL GAME SHOULD BE OVER")
                self.final_score_cmd([])
            self.respond()
        except Exception as e:
          #  player_errors(1)
            #here
            self.respond('{}'.format(str(e)))
            #self.respond("illegal move: {} ".format(str(e)))#+args[1])#+" wrong colour")
            pass
            
            

    def final_score_cmd(self, args):
        self.respond("Final Score: " + self.board.final_score(self.komi))
        self.respond("Thanks for playing, Goodbye.")
        self.respond("ＡＥＳＴＨＥＴＩＣ")
        quit()

    def genmove_cmd(self, args):
        """
        generate a move for the specified color

        Arguments
        ---------
        args[0] : {'b','w'}
            the color to generate a move for
            it gets converted to  Black --> 1 White --> 2
            color : {0,1}
            board_color : {'b','w'}
        """
        try:
            board_color = args[0].lower()
            color = GoBoardUtil.color_to_int(board_color)
            print(color)
            self.debug_msg("Board:\n{}\nko: {}\n".format(str(self.board.get_twoD_board()),
                                                          self.board.ko_constraint))
            move = self.go_engine.get_move(self.board, color)
            if move is None:
                self.respond("pass")
                self.respond("Lol no moves left GG gtfo with that pass bullshit.")
                self.final_score_cmd([])
                #quit()
                #return

            if not self.board.check_legal(move, color):
                move = self.board._point_to_coord(move)
                board_move = GoBoardUtil.format_point(move)
                self.respond("Illegal move: {}".format(board_move))
                raise RuntimeError("Illegal move given by engine")

            # move is legal; play it
            self.debug_msg("Color: " + board_color + " ")
           # print("in genmove_cmd")
            self.board.move(move,color)
            self.debug_msg("Move: {}\nBoard: \n{}\n".format(move, str(self.board.get_twoD_board())))
            move = self.board._point_to_coord(move)
            board_move = GoBoardUtil.format_point(move)
            self.respond(board_move)
            ##############
            #print("AT THE FINAL STATEMENT")
            if GoBoardUtil.generate_random_move(self.board, GoBoardUtil.opponent(color)) == None:
                #print("IN THE FINAL GAME SHOULD BE OVER")
                self.final_score_cmd([])
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

'''
#input:
  issue: int, representing which error
     1: occupied - stone already there
     2: wrong number of args - eg 'play c3'
     3: wrong colour - eg 'play f a1'
     4: wrong coordinate - eg "play w a99'
     5: capture - taking last liberty 
     6: suicide
 color: int, representing the color
 c: int, coordinates of play
 args: string. contains color and coords
  

'''
def player_errors(issue, color, c, args):
    arg=args[0]
    if issue == 1:
        print('illegal move: %s %s alread occupied'%(GoBoardUtil.int_to_color(color), coord_to_position(c)))
    elif issue == 2:
        print(' ', arg, " wrong number of arguments") 
    elif issue == 3:
        print('  %s wrong color'%coord_to_position(c))
    elif issue == 4:
        print('illegal move: [colour] [locaton] wrong coordinate')
    elif issue == 5:
        print('illegal move: [colour] [locaton] captures')
    elif issue == 6:
        print('illegal move: [colour] [locaton] alread occupied')
    else:
        print('bruh whatd you do')

def coord_to_position(coord):
    column_letters = "abcdefghjklmnopqrstuvwxyz"
    if coord is None:
        return "pass"
    row, col = coord
    if not 0 <= row < 25 or not 0 <= col < 25:
        raise ValueError
        #print("yo waddup")
    return column_letters[col-1]+ str(row) 
            


