# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util
import copy


class Grid:

    # this class is from solution to practical 5
    #
    # Note that it creates variables:
    # grid:   an array that has one position for each element in the grid.
    # width:  the width of the grid
    # height: the height of the grid
    #
    # Grid elements are not restricted, so you can place whatever you
    # like at each location. You just have to be careful how you
    # handle the elements when you use them.
    def __init__(self, width, height):
        self.width = width
        self.height = height
        subgrid = []
        for i in range(self.height):
            row=[]
            for j in range(self.width):
                row.append(0)
            subgrid.append(row)
        self.grid = subgrid # create a height*width grid with zeros

    # Set and get the values of specific elements in the grid.
    # Here x and y are index of a state.
    def setValue(self, x, y, value):
        self.grid[y][x] = value

    def getValue(self, x, y):
        return self.grid[y][x]

    # Return width and height to support functions that manipulate the
    # values stored in the grid.
    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width

    # Print the grid out.
    def display(self):
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[i][j],
            # A new line after each line of the grid
            print
        # A line after the grid
        print

    # The display function prints the grid out upside down. This
    # prints the grid out so that it matches the view we see when we
    # look at Pacman.
    def prettyDisplay(self):
        for i in range(self.height):
            for j in range(self.width):
                # print grid elements with no newline
                print self.grid[self.height - (i + 1)][j],
            # A new line after each line of the grid
            print
        # A line after the grid
        print



class MDPAgent(Agent):
    def __init__(self):
        pass
     
   
    def registerInitialState(self, state):
        print api.whereAmI(state)

        # get the size of layout.
        cornertuple = api.corners(state)
        self.width = cornertuple[3][0] + 1    # get the maximum row of the map by using the corners' coordinates
        self.height = cornertuple[3][1] + 1   # get the maximum col of the map by using the corners' coordinates
        print cornertuple[3]
        
        # create variables to store data
        self.foodList = [] # information of foods in the map
        self.wallList = [] # information of wall in the map
        self.capsuleList = [] # information of 4 capsules in the map
        self.visited = [] # store states pacman has visited

        # Create a grid according to the height and width of the data from api.py and fill it with 0s
        self.grid = {}
        for x in range(self.width):  # the horizontal size
             for y in range(self.height):# the vertical size
                 self.grid[(x,y)] = 0
#

    def createValueGrid(self, state): 
        # This function assigns value to each cell depending on the object

        # Get the tuple of pacman, food, capsule, ghost using api
        self.agentstate = api.whereAmI(state) # return state where pacman currently is 
        food = api.food(state) # return state where food currently is 
        capsule = api.capsules(state)
        self.ghostList = api.ghosts(state) 
        wall = api.walls(state)

         # add new food,capsle,wall coordinate to self.xxxx[]
        for f in food:
            if f not in self.foodList:  
                self.foodList.append(f) 
        for f in capsule:
            if f not in self.capsuleList:
                self.capsuleList.append(f)
        for f in wall:
            if f not in self.wallList:
                self.wallList.append(f)

        # Create a list to record the place which pacman already visited
        if self.agentstate not in self.visited:
            self.visited.append(self.agentstate)

        # Assign a reward to each state depending on the object on it

        for i in self.foodList:
            self.grid[i] = 5  # make value on place where has food to 5
            if i in self.visited:
                self.grid[i] = 0  # change foods value on place visited to 0
        
        for i in self.capsuleList:
            self.grid[i] = 7 # make value on place where has capsule to 7
            if i in self.visited:
                self.grid[i] = 0 # change capsule value on place visited to 0
        
        for g in self.ghostList:
            self.grid[int(g[0]),int(g[1])] = -10 # make value on place where has ghost to -10
        
        for i in self.wallList: # assign 'wall' to cell where has a wall
            self.grid[i] = 'wall'

 
    def getUtility(self, position, grid):
        # This function calculates the utility for each cell and returns the maximum utility with its direction
        # initialize utility dictionary
        utility = {'north': 0, 'east':0, 'south':0, 'west':0} #

        pacman = grid[(position[0],position[1])] #define where pacman currently is
        north = grid[(position[0],position[1]+1)]# define the direction change in state of pacman
        east = grid[(position[0]+1,position[1])]
        south = grid[(position[0],position[1]-1)]
        west = grid[(position[0]-1,position[1])]

        # send utilities to a temporal variables utility_xx

        # If the adjacent cell is not a wall, use the value of that cell
        # If it is a wall, use the value of the current cell

        # north
        if north != 'wall': # If north cell is not a wall, use the value of north cell
            utility_north = north * api.directionProb
        else: # If north cell is a wall, use the value of pacman current state
            utility_north = pacman * api.directionProb

        # If west cell is not a wall, 
        #  the change of want to head west but go to north by mistake is (1-api.directionProb)/2
        if west != 'wall':  
            utility_north += west * (1-api.directionProb)/2
        # If west cell is a wall, pacman will stay 
        else:
            utility_north += pacman * (1-api.directionProb)/2

        if east != 'wall':
            utility_north += east * (1-api.directionProb)/2
        else:
            utility_north += pacman * (1-api.directionProb)/2
        utility['north'] = utility_north

        # south
        if south != 'wall':
            utility_south = south * api.directionProb
        else:
            utility_south = pacman * api.directionProb
        if west != 'wall':
            utility_south += west * (1-api.directionProb)/2
        else:
            utility_south += pacman * (1-api.directionProb)/2
        if east != 'wall':
            utility_south += east * (1-api.directionProb)/2
        else:
            utility_south += pacman * (1-api.directionProb)/2
        utility['south'] = utility_south

        # east
        if east != 'wall':
            utility_east = east * api.directionProb
        else:
            utility_east = pacman * api.directionProb
        if north != 'wall':
            utility_east += north * (1-api.directionProb)/2
        else:
            utility_east += pacman * (1-api.directionProb)/2
        if south != 'wall':
            utility_east += south * (1-api.directionProb)/2
        else:
            utility_east += pacman * (1-api.directionProb)/2
        utility['east'] = utility_east

        # west
        if west != 'wall':
            utility_west = west * api.directionProb
        else:
            utility_west = pacman * api.directionProb
        if north != 'wall':
            utility_west += north * (1-api.directionProb)/2
        else:
            utility_west += pacman * (1-api.directionProb)/2
        if south != 'wall':
            utility_west += south * (1-api.directionProb)/2
        else:
            utility_west += pacman * (1-api.directionProb)/2
        utility['west'] = utility_west

        # Return maximum utility and its direction
        max_utility = max(utility.values())
        direction = list (utility.keys()) [list (utility.values()).index(max_utility)]
        return utility
    

    def valueIteration(self, state):
        # This function runs value iteration and calculate the utility of each
        # cells which is not included in excludeList

        # Get excludeList
        update = []
        food = api.food(state)
        for g in self.ghostList:
            for i in range(5):
                for j in range(5):
                    if (int(g[0])+i, int(g[1])+j) not in self.ghostList and (int(g[0])+i, int(g[1]+j)) not in update:
                        update.append((int(g[0])+i, int(g[1])+j))
                    if (int(g[0])+i, int(g[1])-j) not in self.ghostList and (int(g[0])+i, int(g[1])-j) not in update:
                        update.append((int(g[0])+i, int(g[1])-j))
                    if (int(g[0])-i, int(g[1])+j) not in self.ghostList and (int(g[0])-i, int(g[1])+j) not in update:
                        update.append((int(g[0])-i, int(g[1])+j))
                    if (int(g[0])-i, int(g[1])-j) not in self.ghostList and (int(g[0])-i, int(g[1])-j) not in update:
                        update.append((int(g[0])-i, int(g[1])-j))
        
   
        excludeList = []
        for f in food:
            if f not in excludeList and f not in update:
                excludeList.append(f)

        # This function creates a list of cells which must be excluded from
        # the utility calculations

        # Exclude  walls ghosts and from calculation
        # Run value iteration
        for i in range(40):
            old_grid = self.grid.copy()
            for x in range(self.width-1):
                for y in range(self.height-1):
                    if (x,y) not in excludeList and (x,y) not in self.wallList and (x,y) not in self.ghostList:
                        utility = self.getUtility((x,y), old_grid)
                        self.grid[(x,y)] = -1 + 0.7* max(utility.values()) #Bellman Equation
                    

    def getAction(self, state):
        # Get the list of legal actions
        legal = api.legalActions(state)

        # Assign the initial value to the grid
        self.createValueGrid(state)

        # Run value iteration
        self.valueIteration(state)

        # Run calcUtility() once and get the direction with maximum utility
        utility = self.getUtility(self.agentstate, self.grid)
        max_utility = max(utility.values())
        direction = list (utility.keys()) [list (utility.values()).index(max_utility)]

        # makemove by using function makeMove()
        if direction == "north":
            return api.makeMove(Directions.NORTH ,legal)
        if direction == "east":
            return api.makeMove(Directions.EAST ,legal)
        if direction == "south":
            return api.makeMove(Directions.SOUTH ,legal)
        if direction == "west":
            return api.makeMove(Directions.WEST ,legal)
 
