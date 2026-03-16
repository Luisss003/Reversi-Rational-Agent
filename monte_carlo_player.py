#Zijie Zhang, Sep.24/2023

import numpy as np
import socket, pickle
from reversi import reversi
from random import choice
import time
import math
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

        x = -1
        y = -1
        x,y = get_best_move(turn, board, game.directions)

        #Send your move to the server. Send (x,y) = (-1,-1) to tell the server you have no hand to play
        game_socket.send(pickle.dumps([x,y]))

#Class for nodes in Monte Carlo Tree Search.
class Nodes:
    def __init__(self, move, parent, turn, board) -> None:
        self.move = move
        self.parent = parent

        self.turn = turn
        self.board = board

        self.children = []
        self.wins = 0
        self.visits = 0

        self.untried_moves = get_legal_moves(board, turn)

#Wrapper function that initially calls on monte-carlo for start/mid game, and minimax for endgame
def get_best_move(turn, board, directions):
    empty_squares = np.sum(board == 0)

    if empty_squares <= 10:
        score, best_move = minimax_endgame(board, turn, turn, -math.inf, math.inf, directions)
        if best_move is None:
            return -1, -1
        return best_move
    else:
        return monte_carlo(turn, board, directions)
    
#Monte Carlo Tree Search implementation
def monte_carlo(turn, board, directions):
    possible_moves = get_legal_moves(board, turn)
    
    if not possible_moves:
        return -1, -1

    #Reflexively take corners
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for move in possible_moves:
        if move in corners:
            return move
    
    root = Nodes(None, None, turn, board)

    start_time = time.time()
    time_limit = 4.5

    while time.time() - start_time < time_limit:
        node = root

        #Selection: Traverse tree by picking optimal node using UCB1 value.
        while not node.untried_moves and node.children:
            node = max(node.children, key=lambda c: (c.wins / c.visits) + 1.41 * math.sqrt(math.log(node.visits) / c.visits))

        #Expansion: Apply random move to expand tree until leaf node is reached. Add new node to tree.
        if node.untried_moves:
            move = choice(node.untried_moves)
            node.untried_moves.remove(move)

            next_board = np.copy(node.board)
            next_board = local_step(next_board, move[0], move[1], node.turn, directions)
            
            child = Nodes(move, node, -node.turn, next_board)
            node.children.append(child)
            node = child
        
        #Simulation: from the leaf node, simulate a random game until the end and get the result
        result = rollout(node.board, node.turn, directions)

        #Backpropagation: update the nodes on the path from the leaf node to the root with the result of the simulation
        while node is not None:
            node.visits += 1
            if result == -node.turn:
                node.wins += 1
            elif result == 0:
                node.wins += 0.5
            node = node.parent
    

    #Picks a random move if no simulations were run for whatever reason
    if not root.children:
        return choice(possible_moves)
    
    #Otherwise, pick the move with the most visits
    best_child = max(root.children, key=lambda c: c.visits)
    return best_child.move

#Minimax implementation with alpha/beta pruning for endgame.
def minimax_endgame(board, curr_turn, my_turn, alpha, beta, directions, pass_count=0):
    #Base case: no moves or board is full, return winner
    if pass_count == 2 or np.sum(board == 0) == 0:
        my_pieces = np.sum(board == my_turn)
        opponent_pieces = np.sum(board == -my_turn)
        return my_pieces - opponent_pieces, None
    
    legal_moves = get_legal_moves(board, curr_turn)

    #If no legal moves, pass turn to opponent.
    if not legal_moves:
        score, _ = minimax_endgame(board, -curr_turn, my_turn, alpha, beta, directions, pass_count + 1)
        return score, None
    best_move = None

    #Maximizing for my_turn, minimizing for opponent
    if curr_turn == my_turn:
        max_eval = -math.inf
        for move in legal_moves:
            next_board = local_step(np.copy(board), move[0], move[1], curr_turn, directions)
            eval_score, _ = minimax_endgame(next_board, -curr_turn, my_turn, alpha, beta, directions, 0)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)

            if beta <= alpha:
                break
        return max_eval, best_move
    #Minimizing 
    else:
        min_eval = math.inf
        for move in legal_moves:
            next_board = local_step(np.copy(board), move[0], move[1], curr_turn, directions)
            eval_score, _ = minimax_endgame(next_board, -curr_turn, my_turn, alpha, beta, directions, 0)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)

            if beta <= alpha:
                break
        return min_eval, best_move
        
#Simulates a random game until the end and returns the result (1 for white win, -1 for black win, 0 for draw)
#Create a copy of the global board, and then pick favorable moves for each turn until end of game
#Return winner of the simulated game.
def rollout(board, turn, directions):
    temp_board = np.copy(board)
    temp_turn = turn
    pass_count = 0

    while pass_count < 2:
        legal_moves = get_legal_moves(temp_board, temp_turn)

        if len(legal_moves) == 0:
            pass_count += 1
            temp_turn = -temp_turn
            continue
        else:
            pass_count = 0
            move = favor_move(legal_moves, temp_board)
            temp_board = local_step(temp_board, move[0], move[1], temp_turn, directions)
            temp_turn = -temp_turn
    
    white_count = np.sum(temp_board == 1)
    black_count = np.sum(temp_board == -1)

    return 1 if white_count > black_count else -1 if black_count > white_count else 0

def favor_move(legal_moves, board):
    corners = [(0,0), (0,7), (7,0), (7,7)]

    danger_zones = {
        (0, 0): [(0, 1), (1, 0), (1, 1)],
        (0, 7): [(0, 6), (1, 7), (1, 6)],
        (7, 0): [(6, 0), (7, 1), (6, 1)],
        (7, 7): [(7, 6), (6, 7), (6, 6)]
    }

    avail_corners = []
    safe_moves = []
    danger_moves = []

    for move in legal_moves:
        if move in corners:
            avail_corners.append(move)
            continue
        is_danger = False
        for corner, dangers in danger_zones.items():
            if move in dangers:
                if board[corner[0],corner[1]] == 0:
                    is_danger = True
                break
        if is_danger:
            danger_moves.append(move)
        else:
            safe_moves.append(move)

    if avail_corners:
        return choice(avail_corners)
    elif safe_moves:
        return choice(safe_moves)
    else:
        return choice(danger_moves)

#Aggregates legal moves
def get_legal_moves(board, turn):
    legal_moves = []
    for i in range(8):
        for j in range(8):
            if is_legal(board, i, j, turn, game.directions):
                legal_moves.append((i,j))
    return legal_moves

#Determine is a move is legal based on rules of Reversi
def is_legal(board, x, y, piece, directions):
    #Illegal if square is already occupied
    if board[x,y] != 0:
        return False
    
    for dx, dy in directions:
        cursor_x, cursor_y = x + dx, y + dy
        flip_list = []
        #Square must be adjacent to opponent piece + 
        #must be a continuous line of opponent pieces followed by one of your pieces in order to be legal    
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

#Basically stripped down vers of local_step func in reversi.py
#Updates board state after a move and returns the new board only. Used for simulation
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