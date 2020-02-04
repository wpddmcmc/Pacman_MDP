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

class MDPAgent(Agent):
    """Use Markov decision process (MDP) to nevigate pacman
    6CCS3AIN Artificial Intelligence Reasoning and Decision Making Coursework
    Author: Mingcong Chen           ID: K19007740
    EMail: mingcong.chen@kcl.ac.uk
    Date: 23/Nov/2019
    URL: http://www.tgeek.tech/     GitHub: https://github.com/wpddmcmc
    """
    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!" 
        name = "Pacman"
    # Gets run after an MDPAgent object is created and once there is
    # game state to access.

        # Lists to store useful informations
        self.detected_position = []
        self.foods_position = []
        self.capsules_position = []
        self.walls_position = []

    def registerInitialState(self, state):
        print "Running MDPAgent Pacman!"

    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

        # Clear all storage data before next time run
        self.detected_position = []
        self.foods_position = []
        self.capsules_position = []
        self.walls_position = []
	
    def mapSize(self, state):
        """Get the size of layout.

        Calculate the maximum of row and col of the map by using the corners' coordinates

        Args:
            state: The state of an agent (configuration, speed, scared, etc).

        Returns:
            The maximum index of row and maximum index of col
        """
        # unzip corners tuple to two list [col indexs] [row indexs]
        # and then zip two list to tuple [(col indexs)(row indexs)]
        corners = zip(*(api.corners(state)))   
        # return the maximum col index and row index
        return max(corners[0]), max(corners[1])

    def mapUpdate(self, state):
        """Update the value map after once move

        Args:
            state: The state of an agent (configuration, speed, scared, etc).

        Returns:
            The new value map
        """
        # Get the new information from pacman
        food = api.food(state)
        walls = api.walls(state)
        capsules = api.capsules(state)
        ghosts = api.ghosts(state)
        pacman = api.whereAmI(state)

        # If the coordinate pacman not visited before, then store it in to list
        if pacman not in self.detected_position:
            self.detected_position.append(pacman)

        # If the food not be ate before, then store it in to list
        for n in food:
            if n not in self.foods_position:
                self.foods_position.append(n)

        # If the capsules not be ate before, then store it in to list
        for n in capsules:
            if n not in self.capsules_position:
                self.capsules_position.append(n)

        # If the wall not be seen before, then store it in to list
        for n in walls:
            if n not in self.walls_position:
                self.walls_position.append(n)

        # The value map dictionariy
        # The value of foods is 5
        # The value of capsules is 5
        # The value of walls is -5 (but will not be used)
        updated_map = {}
        updated_map.update(dict.fromkeys(self.foods_position, 5))
        updated_map.update(dict.fromkeys(self.capsules_position, 5))
        updated_map.update(dict.fromkeys(self.walls_position, -5))

        edge = self.mapSize(state)  # get the size of the map

        # Update the value map and fill the value map with 0
        # The unknow positions (pacman cannot see) will be set to 0
        for i in range(edge[0]):
            for j in range(edge[1]):
                if (i, j) not in updated_map.keys():
                    updated_map[(i,j)]=0
        # If the food was eatn update with 0
        for n in self.foods_position:
            if n in self.detected_position:
                updated_map[n] = 0
        # If the capsules was eatn update with 0
        for n in self.capsules_position:
            if n in self.detected_position:
                updated_map[n] = 0
        # Set the position of ghosts to -100
        if ghosts:
            for g in ghosts:
                # Tthe ghosts is in another thread, there might be float number
                updated_map[(round(g[0]),round(g[1]))] = -100
        
        return updated_map
                            
    def Iteration(self,state,map,map_type):
        """Use Bellman equation to iterate to update the value map

        Args:
            state: The state of an agent (configuration, speed, scared, etc).
            map: The value map before update
            map_type: the layout- medium one or small one

        Returns:
            The value map after updated by using Bellman function
        """
        # Parameters of Bellman equation
        reward = -1     # reward for every state
        gama = 0.8      # discount factor

        # Get new informations from pacman
        ghosts = api.ghosts(state)
        food = api.food(state)
        capsules = api.capsules(state)
        walls = api.walls(state)

        # The list hold the coordinate that near the ghost (whithin 5 steps in 
        # medium class and 3 steps in small class). The coordinate stored in 
        # the list need to be update by Bellman equation.
        near_ghost = []
        
        # And a nagtive value will be set to the near ghost coordinate to make
        # pacman stay away the areas. The value is -10*(6-distance) with ghost for
        # medium class if within 3 steps and -15*(3-distance) with ghost for small
        # class if within 2 steps.

        # For medium class
        if map_type=='medium':
            for g in ghosts:
                # The ghosts is in another thread, there might be float number
                g_int = (round(g[0]),round(g[1]))
                # did the value update passed a wall? 0-No 1-Yes.
                # If there is a wall between the position and ghost
                # the value will not be set if the position is not at same side of the wall 
                walls_flag = [0,0,0,0,0,0,0,0]  # 0-right, 1- left, 2- up, 3-down, 4-up right, 5- up left, 6- down right, 7- down left
                for i in range(5):
                    # right
                    near_ghost_position = (int(g_int[0]+i), int(g_int[1]))
                    # set nagetive value
                    if i <=3 and near_ghost_position not in walls and near_ghost_position not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i)  
                        if near_ghost_position in walls:
                            walls_flag[0] = 1

                    # left
                    near_ghost_position = (int(g_int[0]-i), int(g_int[1]))
                    # set nagetive value
                    if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i)
                        if near_ghost_position in walls:
                            walls_flag[1] = 1

                    # up
                    near_ghost_position = (int(g_int[0]), int(g_int[1])+i)
                    # set nagetive value
                    if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i) 
                        if near_ghost_position in walls:
                            walls_flag[2] = 1

                    # down
                    near_ghost_position = (int(g_int[0]), int(g_int[1])-i)
                    # set nagetive value
                    if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i) 
                        if near_ghost_position in walls:
                            walls_flag[3] = 1

                    # up right
                    near_ghost_position = (int(g_int[0]+i), int(g_int[1]+i))
                    # set nagetive value
                    if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i) 
                        if near_ghost_position in walls:
                            walls_flag[4] = 1

                    # up left
                    near_ghost_position = (int(g_int[0]-i), int(g_int[1]+i))
                    # set nagetive value
                    if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i) 
                        if near_ghost_position in walls:
                            walls_flag[5] = 1
                    # down right
                    near_ghost_position = (int(g_int[0]+i), int(g_int[1]-i))
                    # set nagetive value
                    if i <= 3 and near_ghost_position not in walls and (near_ghost_position) not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i) 
                        if near_ghost_position in walls:
                            walls_flag[6] = 1

                    # down left
                    near_ghost_position = (int(g_int[0]-i), int(g_int[1]-i))
                    # set nagetive value
                    if i <= 3 and near_ghost_position not in walls and (near_ghost_position) not in ghosts and near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        map[near_ghost_position] = -10*(6-i) 
                        if near_ghost_position in walls:
                            walls_flag[7] = 1

                    # position need to be updated
                    for j in range(5):
                        near_ghost_position = (int(g_int[0]+i), int(g_int[1]+j))
                        if near_ghost_position not in near_ghost and walls_flag[0] == 0:
                            near_ghost.append(near_ghost_position)
                        near_ghost_position = (int(g_int[0]+i), int(g_int[1]-j))
                        if near_ghost_position not in near_ghost and walls_flag[0] == 0:
                            near_ghost.append(near_ghost_position)
                        near_ghost_position = (int(g_int[0]-i), int(g_int[1]+j))
                        if near_ghost_position not in near_ghost and walls_flag[0] == 0:
                            near_ghost.append(near_ghost_position)
                        near_ghost_position = (int(g_int[0]-i), int(g_int[1]-j))
                        if near_ghost_position not in near_ghost and walls_flag[0] == 0:
                            near_ghost.append(near_ghost_position)

        # For small class
        else:
            for g in ghosts:
                # The ghosts is in another thread, there might be float number
                g_int = (round(g[0]),round(g[1]))
                walls_flag = [0,0,0,0,0,0,0,0]      
                for i in range(3):
                    # right
                    near_ghost_position = (int(g_int[0]+i), int(g_int[1]))
                    if near_ghost_position not in near_ghost and walls_flag[0] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <=3 and near_ghost_position not in walls and near_ghost_position not in ghosts:
                            map[near_ghost_position] = -10*(3-i)  
                        if near_ghost_position in walls:
                            walls_flag[0] = 1
                    # left
                    near_ghost_position = (int(g_int[0]-i), int(g_int[1]))
                    if near_ghost_position not in near_ghost and walls_flag[1] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts:
                            map[near_ghost_position] = -10*(3-i)
                        if near_ghost_position in walls:
                            walls_flag[1] = 1
                    # up
                    near_ghost_position = (int(g_int[0]), int(g_int[1])+i)
                    if near_ghost_position not in near_ghost and walls_flag[2] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts:
                            map[near_ghost_position] = -10*(3-i) 
                        if near_ghost_position in walls:
                            walls_flag[2] = 1
                    # down
                    near_ghost_position = (int(g_int[0]), int(g_int[1])-i)
                    if near_ghost_position not in near_ghost and walls_flag[3] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts:
                            map[near_ghost_position] = -10*(3-i) 
                        if near_ghost_position in walls:
                            walls_flag[3] = 1
                    # up right
                    near_ghost_position = (int(g_int[0]+i), int(g_int[1]+i))
                    if near_ghost_position not in near_ghost and walls_flag[4] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts:
                            map[near_ghost_position] = -10*(3-i) 
                        if near_ghost_position in walls:
                            walls_flag[4] = 1
                    # up left
                    near_ghost_position = (int(g_int[0]-i), int(g_int[1]+i))
                    if near_ghost_position not in near_ghost and walls_flag[5] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <= 3 and near_ghost_position not in walls and near_ghost_position not in ghosts:
                            map[near_ghost_position] = -10*(3-i) 
                        if near_ghost_position in walls:
                            walls_flag[5] = 1
                    # down right
                    near_ghost_position = (int(g_int[0]+i), int(g_int[1]-i))
                    if near_ghost_position not in near_ghost and walls_flag[6] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <= 3 and near_ghost_position not in walls and (near_ghost_position) not in ghosts:
                            map[near_ghost_position] = -10*(3-i) 
                        if near_ghost_position in walls:
                            walls_flag[6] = 1
                    # down left
                    near_ghost_position = (int(g_int[0]-i), int(g_int[1]-i))
                    if near_ghost_position not in near_ghost and walls_flag[7] == 0:
                        near_ghost.append(near_ghost_position)
                        # set nagetive value
                        if i <= 3 and near_ghost_position not in walls and (near_ghost_position) not in ghosts:
                            map[near_ghost_position] = -10*(3-i) 
                        if near_ghost_position in walls:
                            walls_flag[7] = 1   
            
        # If there is food and not near the ghost. The coordinate no need to update
        noupdate = []
        for f in food:
            if f not in near_ghost:
                noupdate.append(f)

        # Iteration times for medium class is 40, 20 for small class
        if map_type=='medium':
            loop_count = 40
        else:
            loop_count = 20

        edge = self.mapSize(state)
        while loop_count>0:
            temp_map = map   
            # avoid the coordinate out of map range
            for i in range(edge[0]):
                for j in range(edge[1]):
                    # Iterate the value map by Bellman equation if needed
                    if (i,j) not in walls and (i,j) not in noupdate and (i,j) not in ghosts and (i,j) not in capsules:
                        utilities = self.utility_caculation((i,j),temp_map)
                        # Take the maximum utility of four directions as the utility at (i,j)
                        map[(i,j)] = reward + gama*max(utilities.values())
            loop_count -=1
        return map

    def utility_caculation(self,position,map):
        """Calculate the utility

        Args:
            position: the coodrite need to update the utility
            map: The value map before update

        Returns:
            The utility at position
        """
        # The utility of four directions
        utiluties = {"north_u": 0.0, "south_u": 0.0, "east_u": 0.0, "west_u": 0.0}
        # Next position
        north = (position[0],position[1]+1)
        south = (position[0],position[1]-1)
        west = (position[0]-1,position[1])
        east = (position[0]+1,position[1])
        stay = position

        # policy probability: pi(A/S) = {0.7,0.1,0.1,0.1}

        # If there is a wall at the move directions, use the utility of staying
        # If not a wall, use the utility next position

        # If move to north
        if map[north] != -5:
            north_u = (0.7*map[north])
        else:
            north_u = (0.7*map[stay])
        if map[east] != -5:
            north_u += (0.1*map[east])
        else:
            north_u += (0.1*map[stay])
        if map[west] != -5:
            north_u += (0.1*map[west])
        else:
            north_u += (0.1*map[stay])
        if map[south] != -5:
            north_u += (0.1*map[south])
        else:
            north_u += (0.1*map[south])

        utiluties["north_u"] = north_u
        
        # If move to south
        if map[south] != -5:
            south_u = (0.7*map[south])
        else:
            south_u = (0.7*map[stay])
        if map[east] != -5:
            south_u += (0.1*map[east])
        else:
            south_u += (0.1*map[stay])
        if map[west] != -5:
            south_u += (0.1*map[west])
        else:
            south_u += (0.1*map[stay])
        if map[north] != -5:
            south_u += (0.1*map[north])
        else:
            south_u += (0.1*map[north])

        utiluties["south_u"] = south_u

        # If move to east
        if map[east] != -5:
            east_u = (0.7*map[east])
        else:
            east_u = (0.7*map[stay])
        if map[north] != -5:
            east_u += (0.1*map[north])
        else:
            east_u += (0.1*map[stay])
        if map[south] != -5:
            east_u += (0.1*map[south])
        else:
            east_u += (0.1*map[stay])
        if map[west] != -5:
            east_u += (0.1*map[west])
        else:
            east_u += (0.1*map[west])

        utiluties["east_u"] = east_u

        # If move to west
        if map[west] != -5:
            west_u = (0.7*map[west])
        else:
            west_u = (0.7*map[stay])
        if map[north] != -5:
            west_u += (0.1*map[north])
        else:
            west_u += (0.1*map[stay])
        if map[south] != -5:
            west_u += (0.1*map[south])
        else:
            west_u += (0.1*map[stay])
        if map[east] != -5:
            west_u += (0.1*map[east])
        else:
            west_u += (0.1*map[east])

        utiluties["west_u"] = west_u

        return utiluties

    def whichToMove(self,state,map):
        """Get the maximum utility to make move decision

        Args:
            state: The state of an agent (configuration, speed, scared, etc).
            map: The value map before update

        Returns:
            The move direction decision
        """
        pacman = api.whereAmI(state)    # Get pacman position
        utilities = self.utility_caculation(pacman,map);    # Update utility of pacman postion
        # map[pacman] = max(utilities.values())       # Update value map (only use for debug)
        move_desision = max(zip(utilities.values(),utilities.keys()))    # Get the maximum utility and it's ditection
        
        # Return the dicision movement diriction
        if move_desision[1] == 'north_u':
            return Directions.NORTH
        if move_desision[1] == 'south_u':
            return Directions.SOUTH
        if move_desision[1] == 'west_u':
            return Directions.WEST
        if move_desision[1] == 'east_u':
            return Directions.EAST
        
    def getAction(self, state):
        """Get Action of pacman

        Args:
            state: The state of an agent (configuration, speed, scared, etc).
        """
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        cols,rows = self.mapSize(state) # Get the layout size
        # Judge the layout type medium or small
        map_type = 'medium'
        if cols >= 10 and rows >= 10:   
            map_type = 'medium'
        else:
            map_type = 'small'

        # Update value map after pacman moved
        updated_map = self.mapUpdate(state)
        # Update value map with iteration
        updated_map = self.Iteration(state,updated_map,map_type)
    
        # Make move
        return api.makeMove(self.whichToMove(state,updated_map), legal)