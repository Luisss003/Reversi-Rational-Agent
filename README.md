# Reversi-Rational-Agent
Reversi rational agent

# Understanding reversi backend
## greedy_player.py
If our player recieves -1, they play as black; if 1, then white. If 0, then game is over. After performing the move it wants, it returns a pickle.dumps with the coord of where we want to place our piece.


## reversi.py
Initially sets the board with 4 pieces in the middle. 

It takes a step [x,y] from the user:
1. If x,y already has a piece, return -1 indicating invalid move
2. if x,y is out of bounds, return -1 to indicate invalid move
3. If x,y is a valid placement, but causes no flips, its an illegal move
3. Otherwise, we assume a valid move. 

Assuming we place a valid piece:
1. We look in all directions (u/d, l/r, diags) to see if by placing these, we cause any flips, and add them 

Now once we send out our move, if commit is set to False, we don't actually make the move in the game. This allows us to check if a move is legal before actually doing it, which we do by setting commit=flase
## reversi_server.py