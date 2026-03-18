############################################################
# CMPSC/DS 442: Homework 3 
############################################################

student_name = "Hyuntae Jeong"

############################################################
# Imports
############################################################

# Include your imports here, if any are used.
import random
from collections import deque
import copy

############################################################
# Section 1: Dominoes Game
############################################################

def make_dominoes_game(rows, cols):
    return DominoesGame([[False]*cols for _ in range(rows)])

class DominoesGame(object):

    # Required
    def __init__(self, board):
        self.__board = board
        self.__m = len(board)
        self.__n = len(board[0])
        self.inf = 10**100

    def get_board(self):
        return self.__board

    def reset(self):
        self.__board = make_dominoes_game(self.__m, self.__n).get_board()

    def is_legal_move(self, row, col, vertical):
        if vertical:
            if row < self.__m -1 and row >= 0 and col < self.__n and col >= 0:
                if not self.__board[row][col] and not self.__board[row+1][col]:
                    return True
        else:
            if row < self.__m and row >= 0 and col < self.__n - 1 and col >= 0:
                if not self.__board[row][col] and not self.__board[row][col+1]:
                    return True
        return False
        
    def legal_moves(self, vertical):
        for i in range(self.__m):
            for j in range(self.__n):
                if self.is_legal_move(i, j, vertical):
                    yield (i,j)

    def execute_move(self, row, col, vertical):
        #if is_legal_move
        self.__board[row][col]=True
        if vertical:
            self.__board[row+1][col]=True
        else:
            self.__board[row][col+1]=True

    def game_over(self, vertical):
        return len(self.legal_moves(vertical)) == 0

    def copy(self):
        return DominoesGame(copy.deepcopy(self.__board))

    def successors(self, vertical):
        for i, j in self.legal_moves(vertical):
            new = self.copy()
            new.execute_move(i,j,vertical)
            yield (i, j), new

    def get_random_move(self, vertical):
        return random.choice(self.legal_moves(vertical))
    
    def score(self, vertical):
        return len(list(self.legal_moves(vertical))) - len(list(self.legal_moves(not vertical)))
    # Required
    def get_best_move(self, limit, vertical):
        move, score, leaf = self.helper(limit, vertical, True, 0, -self.inf, self.inf)
        return move, score, leaf


    def helper(self, limit, vertical, plr, curr, alpha, beta):
        if curr == limit:
            return None, self.score(vertical), 1
        if plr:
            result_move = None
            result_score = -self.inf
            leaves = 0
            succ = list(self.successors(vertical))
            if len(succ) == 0:
                return None, self.score(vertical), 1
            for move, b in succ:
                if limit != 0:
                    new_move, new_score, new_leaves = b.helper(limit, vertical, not plr, curr+1, alpha, beta)
                    leaves += new_leaves
                    if new_score > result_score:
                        result_move, result_score = (move, new_score)
                    alpha = max(alpha, new_score)
                    if beta <= alpha:
                        break
            return result_move, result_score, leaves
        else:
            result_move = None
            result_score = self.inf
            leaves = 0
            succ = list(self.successors(not vertical))
            if len(list(succ)) == 0:
                return None, self.score(vertical), 1
            for move, b in succ:
                if limit != 0:
                    new_move, new_score, new_leaves = b.helper(limit, vertical, not plr, curr+1, alpha, beta)
                    leaves += new_leaves
                    if new_score < result_score:
                        result_move, result_score = (move, new_score)
                    beta = min(beta, new_score)
                    if beta <= alpha:
                        break
            return result_move, result_score, leaves


# b = [[False]*3 for i in range(3)]
# g = DominoesGame(b)
# g.execute_move(0,1,True)
# print(g.get_best_move(1, False))
# print(g.get_best_move(2, False))


############################################################
# Section 2: Sudoku
############################################################

def sudoku_cells():
    return [(i//9, i%9) for i in range(81)]

def sudoku_arcs():
    cells = sudoku_cells()
    arcs = set([])
    for i in range(9):
        block = [(i, j) for j in range(9)]
        for j in block:
            for k in block:
                if j != k:
                    arcs.add((j,k))
                    arcs.add((k,j))
        block = [(j, i) for j in range(9)]
        for j in block:
            for k in block:
                if j != k:
                    arcs.add((j,k))
                    arcs.add((k,j))
    for i in range(3):
        for j in range(3):
            block = [(i*3+k//3, j*3+k%3) for k in range(9)]
            for ii in block:
                for jj in block:
                    if not (ii, jj) in arcs:
                        if ii != jj:
                            arcs.add((ii,jj))
    return arcs
        
#print(((0,0), (2,2)) in sudoku_arcs())

def read_board(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().split()
        d={}
        for i in range(9):
            for j in range(9):
                if text[i][j] == "*":
                    d[(i,j)]=set(range(1,10))
                else:
                    d[(i,j)] = set([int(text[i][j])])
        return d
#print(read_board("sudoku/sudoku/hw3-easy.txt"))
class Sudoku(object):

    CELLS = sudoku_cells()
    ARCS = sudoku_arcs()

    def __init__(self, board):
        self.__board= board

    def get_board(self):
        return self.__board

    def get_values(self, cell):
        return self.__board[cell]

    def remove_inconsistent_values(self, cell1, cell2):
        removed = False
        if (cell1, cell2) in self.ARCS:
            if len(self.__board[cell2]) == 1:
                val = next(iter(self.__board[cell2]))
                if len(self.__board[cell2]) == 1 and val in self.__board[cell1]:
                    removed=True
                    tmp = self.__board[cell1]
                    tmp.remove(val)
                    self.__board[cell1] = tmp
        return removed
    
    def get_neighbors(self, cell):
        i, j = cell
        res = set([])
        for k in range(9):
            res.add((i,k))
            res.add((k,j))
        i3, j3 = (i//3)*3, (j//3)*3
        for ii in range(i3, i3+3):
            for jj in range(j3, j3+3):
                res.add((ii,jj))
        res.remove(cell)
        return res

    def infer_ac3(self):
        arcQ = deque(self.ARCS)
        while arcQ:
            cell1, cell2 = arcQ.popleft()
            if self.remove_inconsistent_values(cell1, cell2):
                if len(self.__board[cell1]) == 0:
                    return False
                newarc = self.get_neighbors(cell1)
                for i in newarc:
                    if i != cell2 and not i in arcQ:
                        arcQ.append((cell1, i))
        return True
            


    def infer_improved(self):
        while True:
            board_changed = False
            if self.infer_ac3():
                for n in range(1,10):
                    for i in range(9):
                        cnt = 0
                        idx = (-1, -1)
                        for j in range(9):
                            if n in self.__board[(i,j)]:
                                cnt += 1
                                idx = (i, j)
                        if cnt == 1 and len(self.__board[idx])>1:
                            self.__board[idx]=set([n])
                            board_changed = True
                        cnt = 0
                        idx = (-1, -1)
                        for j in range(9):
                            if n in self.__board[(j,i)]:
                                cnt += 1
                                idx = (j, i)
                        if cnt == 1 and len(self.__board[idx])>1:
                            self.__board[idx]=set([n])
                            board_changed = True
                    for i in range(3):
                        for j in range(3):
                            cnt = 0
                            idx = (-1, -1)
                            for ii in range(i*3, i*3+3):
                                for jj in range(j*3, j*3+3):
                                    if n in self.__board[(ii,jj)]:
                                        cnt += 1
                                        idx = (ii, jj)
                            if cnt == 1 and len(self.__board[idx])>1:
                                self.__board[idx]=set([n])
                                board_changed = True
            if not board_changed:
                break
    
    def solved(self):
        for cell in self.CELLS:
            if len(self.__board[cell]) !=1:
                return False
        return True

    def unsolvable(self):
        for cell in self.CELLS:
            if len(self.__board[cell]) == 0:
                return True
        return False
    
    def infer_with_guessing(self):
        self.infer_improved()
        if self.solved():
            return True
        if self.unsolvable():
            return False
        #guess = None
        for cell in self.CELLS:
            if len(self.__board[cell])>1:
                guess = cell
                cand = self.__board[guess]
                for i in cand:
                    backup = copy.deepcopy(self.__board)
                    self.__board[guess] = {i}
                    if self.infer_with_guessing():
                        return True
                    self.__board = backup


# sudoku = Sudoku(read_board("sudoku/sudoku/hw3-hard1.txt"))
# # print(sudoku.get_values((0,3)))
# # print(sudoku.get_values((0,0)))
# # print(sudoku.get_values((0,1)))
# # print(sudoku.get_values((0,4)))

# # for col in [0, 1, 4]:
# #     removed = sudoku.remove_inconsistent_values((0,3), (0,col))
# #     print(removed, sudoku.get_values((0,3)))
# sudoku.infer_with_guessing()

# print(sudoku.get_board())