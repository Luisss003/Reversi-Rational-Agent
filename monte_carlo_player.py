#Zijie Zhang, Sep.24/2023

import numpy as np
import socket, pickle
from reversi import reversi
from random import choice
game = reversi()

def main():
    game_socket = socket.socket()
    game_socket.connect(('127.0.0.1', 33333))

    while True:

        #Receive play request from the server
        #turn : 1 --> you are playing as white | -1 --> you are playing as black
        #board : 8*8 numpy array
        data = game_socket.recv(4096)
        turn, board = pickle.loads(data)

        #Turn = 0 indicates game ended
        if turn == 0:
            game_socket.close()
            return
        
        #Debug info
        print(turn)
        print(board)

        #TODO: hardcode favorable moves like corners and edges, then use monte carlo for the rest of the moves

        x = -1
        y = -1
        x,y = monte_carlo(turn, board, game.directions)

        #Send your move to the server. Send (x,y) = (-1,-1) to tell the server you have no hand to play
        game_socket.send(pickle.dumps([x,y]))

class Nodes:
    def __init__(self, x, y, turn, board) -> None:
        #x,y : the move that leads to this node
        self.x = x
        self.y = y
        
        #turn : 1 --> white's turn | -1 --> black
        self.turn = turn

        self.board = board

        #children : list of Nodes that can be reached from this node
        self.children = []

        #Maintain statistics for each node
        self.visits = 0
        self.wins = 0

def monte_carlo(turn, board, directions):
    possible_moves = get_legal_moves(board, turn)
    
    if not possible_moves:
        return -1, -1

    move_wins = {}

    for move in possible_moves:
        wins = 0
        simulations_per_move = 1000 
        
        #Only account for wins (maximize wins and favor picking that node)
        for _ in range(simulations_per_move):
            result = simulation(move, turn, board, directions)
            if result == turn:
                wins += 1
        
        move_wins[move] = wins

    # Pick the move that had the most wins
    best_move = max(move_wins, key=move_wins.get)
    return best_move


#Create a temp board and simulate a game starting from the given move, returning the winner at the end of the game
#simulation picks random legal moves up to a certain depth, then counts pieces on board to determine winner
def simulation(start_move, start_turn, board, directions):
    temp_board = np.copy(board)

    temp_board = local_step(temp_board, start_move[0], start_move[1], start_turn, directions)

    temp_turn = -start_turn
    pass_count = 0

    while pass_count < 2:
        legal_moves = get_legal_moves(temp_board, temp_turn)

        if len(legal_moves) == 0:
            pass_count += 1
            temp_turn = -temp_turn
            continue
        else:
            pass_count = 0
            move = choice(legal_moves)
            temp_board = local_step(temp_board, move[0], move[1], temp_turn, directions)
            temp_turn = -temp_turn
    
    white_count = np.sum(temp_board == 1)
    black_count = np.sum(temp_board == -1)

    return 1 if white_count > black_count else -1 if black_count > white_count else 0


#Aggregates legal moves
def get_legal_moves(board, turn):
    legal_moves = []
    for i in range(8):
        for j in range(8):
            if is_legal(board, i, j, turn, game.directions):
                legal_moves.append((i,j))
    return legal_moves

#Checks if placing a move is legal based on:
#1. The cell must be empty
#2. There must be at least one straight (horizontal, vertical, or diagonal) occupied
# line between the new piece and another piece of the same color, with one or more contiguous opponent pieces between them
def is_legal(board, x, y, piece, directions):
    if board[x,y] != 0:
        return False
    
    for dx, dy in directions:
        cursor_x, cursor_y = x + dx, y + dy
        flip_list = []
        
        while 0 <= cursor_x <= 7 and 0 <= cursor_y <= 7:
            if board[cursor_x, cursor_y] == 0:
                break
            elif board[cursor_x, cursor_y] == piece:
                if flip_list:
                    return True
                else:
                    break
            else:
                flip_list.append((cursor_x, cursor_y))
                cursor_x += dx
                cursor_y += dy
    return False

#This is essentially the step func in reversi.py, but it simply updates the game board without any score logic
#Used to simulte games in monte carlo without affecting the actual game state
def local_step(board, x, y, piece, directions):
    board[x, y] = piece
    for dx, dy in directions:
        cursor_x, cursor_y = x + dx, y + dy
        flip_list = []
        
        while 0 <= cursor_x <= 7 and 0 <= cursor_y <= 7:
            if board[cursor_x, cursor_y] == 0:
                break
            elif board[cursor_x, cursor_y] == piece:
                for cord_x, cord_y in flip_list:
                    board[cord_x, cord_y] = piece
                break
            else:
                flip_list.append((cursor_x, cursor_y))
                cursor_x += dx
                cursor_y += dy
    return board



if __name__ == '__main__':
    main()