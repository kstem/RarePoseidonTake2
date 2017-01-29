"""
glossary:
    point : int
        coordinate of point on the board
    color : int
        color code of the point represented in interger, imported from board utility
        EMPTY = 0
        BLACK = 1
        WHITE = 2
        BORDER = 3
        FLOODFILL = 4

"""


import numpy as np
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, FLOODFILL 

class GoBoard(object):

    def move(self, point, color):
        """
        Play a move on the board.
        Argumnets:
            point
        Return:
            color
        """
        move_inspection, msg =self._play_move(point,color)
        if not move_inspection:
            return False
        else:
            self.last_played_color = color
            return True

    @staticmethod
    def showboard(board,bd_size):
        #TODO: would be nice to have a nicer printout of the board
        pass


    def get_color(self, point):
        """
        Return the state of the specified point.
        Argumnets:
            point
        Return:
            color
        """
        return self.board[point]

    def check_legal(self,point,color):
        """
        Argumnets:
            point, color
        Return:
            bool
            Whether the playing point with the given color is
            legal.
        """
        sboard = np.array(self.board, copy=True)
        # swap out true board for simulation board, and try to play the move
        result, _=self._play_move(point, color)
        # reset true board; return result
        self.board = sboard
        return result

    def final_score(self,komi):
        """
        Calculate score of board state and return player ID (1, -1, or 0 for tie)
        corresponding to winner. Uses 'Area scoring'.
        Argumnets:
            komi, number of points added to white because of starting second
        Returns:
            score: score of the game in the format of `X+{n}` where is either B or W
            and n is number of points that color has more than the other.
        This function is based of https://github.com/Rochester-NRT/RocAlphaGo/blob/develop/AlphaGo/go.py --> get_winner
        """
        # Count number of positions filled by each player, plus 1 for each eye-ish space owned
        score_white = np.sum(self.board == WHITE)
        score_black = np.sum(self.board == BLACK)
        empties = list(*np.where(self.board == EMPTY))
        for empty in empties:
            # Check that all surrounding points are of one color
            result = self._is_eyeish(empty)
            if result==BLACK:
                score_black += 1
            elif result==WHITE:
                score_white += 1
        score_white += komi
        score_white -= self.passes_white
        score_black -= self.passes_black
        if score_black > score_white:
            self.winner = BLACK
        elif score_white > score_black:
            self.winner = WHITE
        else:
            # Tie
            self.winner = 0
        if self.winner==1:
            result="B+{}".format( score_black - score_white )

        else:
            result="W+{}".format(score_white - score_black )

        return result

    def get_winner(self,komi):
        """
        Returns:
        winner: color code of winner
        """
        if self.winner==None:
            self.final_score(komi)
        return self.winner

    def get_twoD_board(self,):
        """
        Return: numpy array
        a two dimensional numpy array with same values as in the self.board without having the borders
        """
        board = np.zeros((self.size,self.size),dtype=np.int32)
        for i in range(self.size):
            row=(i+1)*self.NS+1
            board[i,:] = self.board[row:row+self.size]
        return board

        
    def get_empty_positions(self, color):
        """
        Argumnets:
            color
        This function return a list of moves for current player.
        Return:
            list of empty poisitions by excluding eye points and KO constraint points 
        """
        moves = []
        for y in range(1,self.size+1,1):
            for x in range(1,self.size+1,1):
                point = self._coord_to_point(x,y)
                if self.get_color(point)!=EMPTY:
                    continue
                if self.is_eye(point,color):
                    continue
                if self.ko_constraint==point:
                    continue
                moves.append(point)
        return moves;


    def __init__(self, size):
        """
        Creates a board that uses 1 dimenstional reperesentaion of for points
        ----------
        This board has the following functionalities:
            1. move :plays a move at given point
            2.
        """
        # initialize using reset since it would be the same code as in __init__
        self.reset(size)


    def reset(self, size):
        """
        Creates an initial board position
        reset the board to a new size

        Arguments
        ---------
        size : int
            size of board to reset to
        """

        self.name = "Board 1D"
        self.version = 0.1
        self.size = size
        self.NS = size + 1
        self.WE=  1
        self.suicide = True # checking for suicide move
        self._is_empty = True
        self.ko_constraint = None
        self.passes_white = 0
        self.passes_black = 0
        self.white_captures = 0
        self.black_captures = 0
        self.current_player= BLACK
        self.last_played_color=None
        self.winner = None
        self._empty_positions = {BLACK:[],WHITE:[]}
        self.maxpoint = size*size + 3*(size+1)  # Attention we are doing zero indexing so everything is of by one
        """
        The array is one-dimensional and this representation is achieved through _coord_to_point function
        This is an example of 3x3 board point numbering (indices of numpy array).
        Spaces are added for illustration to separate board points from border points.
        Note that there is only one point buffer between each row (e.g. point 12).
        
        16   17 18 19   20

        12   13 14 15   16
        08   09 10 11   12
        04   05 06 07   08

        00   01 02 03   04

        and this is how array will look like if we translate it into two dimensional array
        [ 3.,  3.,  3.,  3.,  3.,  0.,  0.,  0.,  3.,  0.,  0.,  0.,  3.,  0.,  0.,  0.,  3.,  3.,  3.,  3.,  3.]

        3  3  3  3  3
        3  0  0  0  3
        3  0  0  0  3
        3  0  0  0  3
        3  3  3  3  3

        """
        self.board = np.ones((self.maxpoint),dtype=np.int16)*BORDER
        self._empty_filling(self.board) 


    def copy(self):
        """Return an independent copy of this Board."""
        b = GoBoard(self.size)
        b.board = np.copy(self.board)
        b.suicide = self.suicide  # checking for suicide move
        b.winner = self.winner
        b.NS = self.NS
        b.WE = self.WE
        b.last_played_color = self.last_played_color
        b._is_empty = self._is_empty
        b.passes_black = self.passes_black
        b.passes_white = self.passes_white
        b.current_player = self.current_player
        b.ko_constraint =  self.ko_constraint
        b.white_captures = self.white_captures
        b.black_captures = self.black_captures 

        return b


    def _empty_filling(self,board):
        """
        Fills points inside board with EMPTY
        Arguments
        ---------
        board : numpy array
            receives a numpy array filled with BORDER

        """
        for ind in range(1,self.size+1,1):
            indices = [j for j in range(ind*self.NS + 1,ind*self.NS+self.size+1,1)]
            np.put(board,indices, EMPTY)


    def is_eye(self,point,color):
        """
        Is eyeish can detect diamond shape around a point if that fails we know that is not an eye
        Arguments
        ---------
        point, color

        Return
        ---------
            eye color or None
            whether the point with given color is inside an eye
        This function is based on https://github.com/pasky/michi/blob/master/michi.py --> is_eye
        """
        eye_color = self._is_eyeish(point)
        if eye_color != color:
            return None
        if eye_color == None:
            return None
        # Eye-like shape, but it could be a falsified eye
        false_color = GoBoardUtil.opponent(eye_color)
        false_count = 0
        at_edge = False
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = True
            elif self.board[d] == false_color:
                false_count += 1
        if at_edge:
            false_count += 1
        if false_count >= 2:
            return None
        return eye_color    
    
        
    """
    ----------------------------------------------------------------------------------------------------------------------
    helper functions for playing a move!
    ----------------------------------------------------------------------------------------------------------------------
    """
    def _is_eyeish(self,point):
        """
        returns whether the position is empty and is surrounded by all stones of the same color.
        Arguments
        ---------
        point

        Return
        ---------
        bool:
             whether the neighbors of the point all have same color
        This is based on https://github.com/pasky/michi/blob/master/michi.py --> is_eyeish
        
        """
        if self.board[point] != EMPTY:
            return None
        first=True
        for n in self._neighbors(point):
            if self.board[n] == BORDER:
                continue
            if self.board[n] == EMPTY:
                return None
            if first:
                eye_color = self.board[n]
                first = False
            else:
                if self.board[n] != eye_color:
                    return None
        return eye_color


    def _liberty(self,point,color):
        """
        ---------
        Return
        ---------
        liberty: int
             Number of liberty that the given point has
        """

        group_points = [point]
        liberty=0
        met_points=[point]
        while group_points:
            p=group_points.pop()
            met_points.append(p)
            neighbors = self._neighbors(p)
            for n in neighbors:
                if self.board[n]==BORDER:
                    continue
                if self.board[n]==color and n not in met_points:
                    group_points.append(n)
                elif self.board[n]==EMPTY and n not in met_points:
                    liberty+=1
        return liberty


    def _liberty_flood(self,board):
        """
        This function find the liberties of flood filled board.
        return True if it finds any liberty and False otherwise
        Arguments
        ---------
        board : numpy array

        Return
        ---------
        bool:
             whether the flood filled group in the board has any liberty
        """
        #cond = board==FLOODFILL
        #inds = np.where(cond)
        inds = list(*np.where(board == FLOODFILL))
        for f in inds:
            f_neighbors = self._neighbors(f)
            found_liberties = board[f_neighbors]==EMPTY
            if found_liberties.any():
                return True
        return False


    def _flood_fill(self, point):
        """
        Creates a new board and fills the connected groups to the given point
        Arguments
        ---------
        point

        Return
        ---------
         a new board with points in the neighbor of given point with same color replaced with
         FLOODFILL(=4)
         This is based on https://github.com/pasky/michi/blob/master/michi.py --> floodfill
        """
        fboard = np.array(self.board, copy=True)
        flood_list=[point]
        color = fboard[point]
        fboard[point] = FLOODFILL
        while flood_list:
            current_point = flood_list.pop()
            neighbors = self._neighbors(current_point)
            for n in neighbors :
                if fboard[n] == color:
                    fboard[n] = FLOODFILL
                    flood_list.append(n)
        return fboard


    def _play_move(self,point, color):
        """
        This function is for playing the move
        Arguments
        ---------
        point, color

        Return
        ---------
        State of move and appropriate message for that move
        """

        if self.board[point] != EMPTY:
            c=self._point_to_coord(point)
            msg = "Row and Column: %d %d is already filled with a %s stone"%(c[0],c[1],GoBoardUtil.int_to_color(color))
            return False,msg
        if point == self.ko_constraint:
            msg ="KO move is not permitted!"
            return False , msg
        self.board[point] = color
        self._is_empty = False
        self.caps = []
        single_captures = []
        cap_inds = None
        neighbors = self._neighbors(point)
        for n in neighbors:
            if self.board[n]==BORDER:
                continue
            if self.board[n]!=color:
                if self.board[n]!=EMPTY:
                    fboard = self._flood_fill(n)
                    if not self._liberty_flood(fboard):
                        cap_inds = fboard==FLOODFILL
                        #self.caps = np.where(fboard==FLOODFILL)
                        self.caps += list(*np.where(fboard==FLOODFILL))
                        num_captures = np.sum(cap_inds)
                        if num_captures == self.size*self.size:
                            self._is_empty = True
                        if num_captures == 1:
                            single_captures.append(n)
                        if color==WHITE:
                            self.white_captures += num_captures
                        else :
                            self.black_captures += num_captures
                        self.board[cap_inds]=EMPTY
        in_enemy_eye = self._is_eyeish(point) != color
        fboard = self._flood_fill(point)
        self.ko_constraint = single_captures[0] if in_enemy_eye and len(single_captures) == 1 else None
        if self._liberty_flood(fboard) and self.suicide:
            #non suicidal move
            c=self._point_to_coord(point)
            msg = "Playing a move with %s color in the row and column %d %d is permited"%(color,c[0],c[1])
            return True, msg
        else:
            # undoing the move because of being suicidal
            self.board[point] = EMPTY
            if cap_inds!= None:
                self.board[cap_inds]=GoBoardUtil.opponent(color)
            c=self._point_to_coord(point)
            msg = "Suicide move with color %s in the row and column: %d %d "%(color, c[0],c[1])
            return False, msg


    def _neighbors(self,point):
        """
        All neighbors of the point
        Arguments
        ---------
        point

        Returns
        -------
        points : list of int
            coordinate of points which are neighbors of the given point
        """
        #row,col = self._point_to_coord(point)
        #if 0 <= row <= self.size+1 and 0 <= col <= self.size+1:
        return [point-1, point+1, point-self.NS, point+self.NS]
        #else:
        #    raise ValueError("This point is out of range!")


    def _diag_neighbors(self,point):
        """
        All diagonal neighbors of the point
        Arguments
        ---------
        point

        Returns
        -------
        points : list of int
            coordinate of points which are diagnoal neighbors of the given point
        """

        #row,col = self._point_to_coord(point)
        #if 0 <= row <= self.size+1 and 0 <= col <= self.size+1:
        return [point-self.NS-1, point-self.NS+1, point+self.NS-1, point+self.NS+1]
        #else:
        #    raise ValueError("This point is out of range!")


    def _border_removal(self,points):
        """
        Removes Border points from a list of points received as Input and Return the result
        as a list
        Arguments
        ---------
        points : list of int
            coordinate of points on the board

        Returns
        -------
        points : list of int
            coordinate of points on the board
        """
        coords=[self._point_to_coord(p) for p in points]
        coords=np.reshape(coords,(-1,2))
        ind=0
        removal=[]
        for c in coords:
            b1=c==0
            b2=c==self.size+1
            if b1.any() or b2.any():
                removal.append(ind)
            ind+=1
        removal=np.unique(removal)
        return list(np.delete(points,removal))

    def _on_board(self, point):
        """
        returns True if point is inside the board and not on the borders.
        Arguments
        ---------
        point

        Returns
        -------
         bool
        """
        return self.board[point]!= BORDER


    def _points_color(self,point):
        """
        Return the state of the specified point.

        Arguments
        ---------
        point

        Returns
        -------
         color: string
                 color representing the specified point .
        """
        p_int_color=self.board[point]
        return GoBoardUtil.int_to_color(p_int_color)

    def _coord_to_point(self,row,col):
        """
        Transform two dimensional presentation to one dimension.

        Arguments
        ---------
         x , y : int
                 coordination of the board  1<= x <=size, 1<= y <=sizeint

        Returns
        -------
        point
        """
        if row <0 or col < 0:
            raise ValueError("Wrong coordinates, Coordinates should be larger than 0")
        return self.NS*row + col

    def _point_to_coord(self,point):
        """
        Transform one dimension presentation to two dimensional.

        Arguments
        ---------
        point

        Returns
        -------
        x , y : int
            coordination of the board  1<= x <=size, 1<= y <=size .
        """
        if point is None:
            return 'pass'
        row, col = divmod(point, self.NS)
        return row,col

