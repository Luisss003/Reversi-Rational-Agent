#Zijie Zhang, Sep.24/2023

import numpy as np
import socket, pickle
from reversi import reversi

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

        #We want to initially favor the edges of the board
        x = -1
        y = -1
        monte_carlo(x,y, turn, board)

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

def monte_carlo(x, y, turn, board):
    #Create a current state of the game
    curr_state = Nodes(x,y,turn, board)

    #Now, we need to simulate the different possible moves and add them to children list
    simulation(curr_state, board)
    pass

def simulation(curr_state, board):
    #First, copy the current state of the board
    temp_board = curr_state.board

    #While the game isn't finished, we want to aggregate legal moves

    #if we, and the other player have no legal moves, that indicates the end of the game
    

#Based on win count of each child node of the curr state, pick the most promising child 
def selection(current_state):
    contender = Nodes(0,0,0,0)
    for child in current_state.children:
        contender = max(contender.wins, child.wins)

    return contender




if __name__ == '__main__':
    main()