#Import everything
import pygame,pickle,threading,os,copy,math
import tkinter as tk
from tkinter import *

###Class for all components
class Component(pygame.sprite.Sprite):
    #Constructor
    def __init__(self,name,ID,attributes,initialPosition):
        pygame.sprite.Sprite.__init__(self)
        #Name used to identify component type
        self.name = name
        #ID used to identify specific component
        self.ID = ID
        self.pickupStatus = False
        #Sets all existing varibles to be attributes in the component
        #e.g. if the component has passed in in attributes "voltage" it makes an attribute
        variables = vars(self)
        for key in attributes:
            variables[key] = attributes[key]
        self.surf = pygame.image.load(f'graphics/{self.name}Base.png')
        self.image = 'base'
        self.rightClicked = False
        self.rect = self.surf.get_rect(center = initialPosition)
        self.currentPosition = initialPosition
        self.x = self.currentPosition[0]
        self.y = self.currentPosition[1]
        self.left = self.rect.midleft
        self.right = self.rect.midright
        self.top = self.rect.midtop
        self.bottom = self.rect.midbottom
        #Stores connecting points for finding nearest sprite = left/right/top/bottom coords of component image
        self.connectors = {'left': self.left,'right': self.right,'top': self.top,'bottom': self.bottom}
        #Stores connected wireSprites at left/right/top/bottom
        #Wires can only be connected to left/right, but top and bottom are shown to allow voltmeters
        # to find the nearest sprite when left/right are already used.
        self.connected = {'left': None,'right': None,'top': None,'bottom': None}
        #Is sprite part of the circuit graph
        self.active = False
        pygame.sprite.Group.add(self)
        componentSpriteGroup.add(self)
        IDSprites.add(self)
        allSprites.add(self)
        IDTracker.add(self)
        #Add conditional attributes for specific sprites
        if self.name == 'voltmeter':
            self.voltWires = {'left': None, 'right': None}   
        elif self.name == 'thermistor':
            self.prevTemp = 21     
        elif self.name == 'ldr':
            self.prevLI = 500
            self.left = (self.rect.midleft[0],self.rect.midleft[1]+3)
            self.right = (self.rect.midright[0],self.rect.midright[1]+3)
            
    #Update sprite when it is being moved
    def update(self):
        self.left = self.rect.midleft
        self.right = self.rect.midright
        self.top = self.rect.midtop
        self.bottom = self.rect.midbottom
        self.x = self.currentPosition[0]
        self.y = self.currentPosition[1]
        self.connectors = {'left':self.left,'right':self.right,'top':self.top,'bottom':self.bottom}
        if self.name == 'ldr':
            self.left = (self.rect.midleft[0],self.rect.midleft[1]+3)
            self.right = (self.rect.midright[0],self.rect.midright[1]+3)
        if self.name == 'voltmeter':
            if self.voltWires['left'] == None:
                self.pd = 0
            
    #Get every attribute of the component as a dictionary
    def allAttributes(self):
        return vars(self)
    
    #Toggles image between base (black) and red when called for being selected
    def toggleImage(self):
        if self.image == 'base':
            self.image = 'red'
        else:
            self.image = 'base'
        image = self.image.title()
        if self.name == 'lamp':
            if self.active == True:
                self.surf = pygame.image.load(f'graphics/{self.name}{image}On.png')
            else:
                self.surf = pygame.image.load(f'graphics/{self.name}{image}.png')
        elif self.name == 'cell':
            if self.resistance > 0:
                self.surf = pygame.image.load(f'graphics/{self.name}Resistor{image}.png')
                self.rect = self.surf.get_rect(midleft = self.left)
                self.update()
            else:
                self.surf = pygame.image.load(f'graphics/{self.name}{image}.png')
                self.rect = self.surf.get_rect(midleft = self.left)
                self.update()      
        else:
            self.surf = pygame.image.load(f'graphics/{self.name}{image}.png')
            
    #Change current component image to have a blue tint when the mouse is hovering over it
    def hover(self,changeType):
        image = self.image.title()
        if self.name == 'lamp':
            if circuitGraph.circuitValid == True and self.active == True:
                self.surf = pygame.image.load(f'graphics/{self.name}{image}On{changeType}.png')
            else:
                self.surf = pygame.image.load(f'graphics/{self.name}{image}{changeType}.png')          
        elif self.name == 'cell':
            if self.resistance > 0:
                self.surf = pygame.image.load(f'graphics/{self.name}Resistor{image}{changeType}.png')
                self.rect = self.surf.get_rect(center = self.currentPosition)
                self.update()
            else:
                self.surf = pygame.image.load(f'graphics/{self.name}{image}{changeType}.png')
                self.update()
        else:
            self.surf = pygame.image.load(f'graphics/{self.name}{image}{changeType}.png')
                
    #Save current sprite attributes and positions to an actions file for undo/redo
    def save(self,saveType):
        allAttributes = self.allAttributes()
        attributesForPickle = []
        for attribute in allAttributes:
            #Excludes any attributes containing surfaces for serialising
            if attribute != 'surf' and attribute != '_Sprite__g' and attribute != 'connected' and attribute != 'undoneConnectors' and attribute != 'voltWires': 
                attributesForPickle.append({attribute: allAttributes[attribute]})
        #Saves the sprite to "actions[filePointer]" text file by pickling
        with open(f'actionsFolder/action{actions.savedFilePointer}', 'wb') as file:
            pickle.dump(attributesForPickle, file)
        #Move file pointer forwards (if new action)
        if saveType == 'new':
            actions.savedFilePointer += 1
            actions.savedFilePointer = actions.savedFilePointer%actions.maximum
            
    #Undo sprite movement by loading previous file and updating positions
    def undo(self):
        #Save sprite without moving pointer
        self.save('old')
        actions.savedFilePointer -= 1
        if actions.savedFilePointer == -1:
            actions.savedFilePointer += actions.maximum
        #Load previous file
        with open(f'actionsFolder/action{actions.savedFilePointer}', 'rb') as file:
            unPickled = pickle.load(file)
        #Iterate through unpickled file and re-assign/update all attributes
        for attribute in unPickled:
            for attributeName in attribute:
                vars(self)[attributeName] = attribute[attributeName]
        self.pickupStatus = False
        self.x = self.currentPosition[0]
        self.y = self.currentPosition[1]
        self.rect = self.surf.get_rect(center = self.currentPosition)
        self.left = self.rect.midleft
        self.right = self.rect.midright
        self.top = self.rect.midtop
        self.bottom = self.rect.midbottom
        self.connectors = {'left':self.left,'right':self.right,'top':self.top,'bottom':self.bottom}
        #Iterate through "connected" to find any connected wires and update the ends of any existing wires
        for key in self.connected:
            if self.connected[key]:
                wire = self.connected[key]
                if wire.sprites[0] == self:
                    wire.ends[0] = self.connectors[key]
                elif wire.sprites[1] == self:
                    wire.ends[1] = self.connectors[key]
    
    #Redo sprite movement by loading next file and updating positions
    def redo(self):
        #Save sprite without moving pointer
        self.save('old')
        actions.savedFilePointer += 1
        actions.savedFilePointer = actions.savedFilePointer%actions.maximum
        #Load next file
        with open(f'actionsFolder/action{actions.savedFilePointer}', 'rb') as file:
            unPickled = pickle.load(file)
        #Re-assign and update all attributes from loaded file
        for attribute in unPickled:
            for attributeName in attribute:
                vars(self)[attributeName] = attribute[attributeName]
        self.pickupStatus = False
        self.x = self.currentPosition[0]
        self.y = self.currentPosition[1]
        self.rect = self.surf.get_rect(center = self.currentPosition)
        self.left = self.rect.midleft
        self.right = self.rect.midright
        self.top = self.rect.midtop
        self.bottom = self.rect.midbottom
        self.connectors = {'left':self.left,'right':self.right,'top':self.top,'bottom':self.bottom}
        #Update wire end positions
        for key in self.connected:
            if self.connected[key]:
                wire = self.connected[key]
                if wire.sprites[0] == self:
                    wire.ends[0] = self.connectors[wire.spriteConnectors[0]]
                elif wire.sprites[1] == self:
                    wire.ends[1] = self.connectors[wire.spriteConnectors[1]]
    
    #Reset component circuit values when circuit is broken
    def reset(self):
        if self.active == True:
            variables = vars(self)
            atts = globals()[f'{self.name}Attributes']
            for key in atts:
                variables[key] = atts[key]

###Class for Wires
class Wire(pygame.sprite.Sprite):
    #Constructor
    def __init__(self,ID,start,end,inputType):
        pygame.sprite.Sprite.__init__(self)
        self.name = 'wire'
        self.inputType = inputType
        self.ID = ID
        self.end = end
        #Start and end position
        self.ends = [start,end] 
        #Respective start/end sprites
        self.sprites = [None,None] 
        #Respective start/end sprite connectors (left/right)
        self.spriteConnectors = [None,None]
        self.prevData = []
        #Is wire being dragged
        self.placed = False
        self.image = 'base'
        self.color = '#000000'
        allSprites.add(self)
        IDSprites.add(self)
        IDTracker.add(self) 
    
    #Update end of wire when it is no longer being dragged
    def updateEnd(self,nearestPoint,makingWire,wireOriginSprite,wireOriginConnector,):
        #If wire is being dragged, set end to mouse_pos
        if makingWire == True:
            self.ends[1] = pygame.mouse.get_pos()
        else:
            #If there is a non-used connector in 75px:
            if nearestPoint != None:
                if nearestPoint[1] != 'top' and nearestPoint[1] != 'bottom':
                    #Show proxCircle at nearestPoint
                    self.ends[1] = proxCircle.pos
                    self.placed = True
                    wireOriginCon = None
                    nearestCon = None
                    #Find and set [sprites] and [spriteConnectors]
                    for key in wireOriginSprite.connectors:
                        if wireOriginSprite.connectors[key] == self.ends[0]:
                            wireOriginCon = key
                    for key in nearestPoint[0].connectors:
                        if nearestPoint[0].connectors[key] == self.ends[1]:
                            nearestCon = key
                    self.sprites = [wireOriginSprite,nearestPoint[0]]
                    self.spriteConnectors = [wireOriginCon,nearestCon]
                    for key in wireOriginSprite.connected:
                        if wireOriginConnector == key:
                            wireOriginSprite.connected[key] = self
                    for key in nearestPoint[0].connected:
                        if nearestPoint[1] == key:
                            nearestPoint[0].connected[key] = self    
                    #Add wire creation to actions stack
                    actions.add([self,'createdWire'])
                    #Add edge to circuit graph
                    circuitGraph.addEdge(self.sprites[0].ID,self.sprites[1].ID)
                    
    #If component is being moved and wire is placed down, update the end of the wire to follow the component          
    def update(self):
        for sprite in self.sprites:
            if sprite.pickupStatus == True:
                 for key in sprite.connectors:
                     if sprite == self.sprites[0]:
                         self.ends[0] = sprite.connectors[self.spriteConnectors[0]]
                         break
                     elif sprite == self.sprites[1]:
                         self.ends[1] = sprite.connectors[self.spriteConnectors[1]]
                         break
    
    #Get all attributes
    def allAttributes(self):
        return vars(self)
    
    #Reset self     
    def reset(self):
        self.placed = False
        self.sprites = [None,None]
        self.spriteConnectors = [None,None]
        allSprites.remove(self)
        IDSprites.remove(self)
    
    #Undo wire by saving data to prevData attribute and reset attributes
    def undoCreation(self,deletedSprite):
        self.prevData = [copy.copy(self.ends),copy.copy(self.sprites),copy.copy(self.spriteConnectors)]
        for component in self.sprites:
            if component != deletedSprite:
                for key in component.connected:
                    if component.connected[key] == self:
                        component.connected[key] = None
        self.reset()
    
    #Redo wire by re-initialising attirbutes using prevData
    def redoCreation(self):
        self.placed = True
        self.ends = self.prevData[0]
        self.sprites = self.prevData[1]
        self.spriteConnectors = self.prevData[2]
        if self.sprites[0].connected[self.spriteConnectors[0]] == None:
           self.sprites[0].connected[self.spriteConnectors[0]] = self
        if self.sprites[1].connected[self.spriteConnectors[1]] == None:
            self.sprites[1].connected[self.spriteConnectors[1]] = self
        allSprites.add(self)
        IDSprites.add(self)

###Class for red proximity indicator (for when the mouse is hovering near an available connector)
class ProxCircle(pygame.sprite.Sprite):
    #Constructor
    def __init__(self,name,ID,pos):
        pygame.sprite.Sprite.__init__(self)
        self.name = name
        self.ID = ID
        self.pos = pos
        self.surf = pygame.image.load('graphics/proxCircle.png')
        self.rect = self.surf.get_rect(center = self.pos)
    #Set the position of the proxCircle to the closest point available
    def showClosest(self,nearestPoint,wireOrigin):
        if nearestPoint[2] <= 75:
            if nearestPoint[1] == 'left':
                self.rect = self.surf.get_rect(center = nearestPoint[0].left)
                self.pos = nearestPoint[0].left
            elif nearestPoint[1] == 'right':
                self.rect = self.surf.get_rect(center = nearestPoint[0].right)
                self.pos = nearestPoint[0].right

###Class for circular buffer/stack which stores the users previous actions for undo/redo
class Cstack():
    #Constructor
    def __init__(self,name,maximum):
        self.name = name
        self.stack = [None]*maximum
        self.maximum = maximum
        self.front = 0
        self.rear = -1
        self.usedItems = 0
        self.undoneItems = 0
        #File pointer for loading component positions
        self.savedFilePointer = 0
    #Reset stack
    def reset(self):
        self.stack = [None]*self.maximum
        self.front = 0
        self.rear = -1
        self.usedItems = 0
        self.undoneItems = 0
        self.savedFilePointer = 0
        
    #Add action to stack
    def add(self,item):
        #If all slots are used, set front item and update pointers
        if self.usedItems == self.maximum:
            self.stack[self.front] = item
            self.front += 1
            self.rear += 1
            self.front = self.front%self.maximum
            self.rear = self.rear%self.maximum
        else:
            #If not all slots are "used"
            self.usedItems += 1
            self.rear += 1
            self.rear = self.rear%self.maximum
            self.stack[self.rear] = item
        self.undoneItems = 0
        if self.stack[self.rear][1] != 'createdComponent':
            self.action()
        
    #Undo action in stack
    def undo(self):
        actionUndone = self.stack[self.rear]
        #If stack not empty
        if self.usedItems > 0:
            self.usedItems -= 1
            self.undoneItems += 1
            self.rear -= 1
            if self.rear == -1:
                self.rear += self.maximum
            if actionUndone != None:
                undoneSprite = actionUndone[0]
                #Undo component creation
                if actionUndone[1] == 'createdComponent':
                    allSprites.remove(undoneSprite)
                    IDSprites.remove(undoneSprite)
                    componentSpriteGroup.remove(undoneSprite)
                    circuitGraph.removeNode(undoneSprite.ID)
                #Undo component movement
                elif actionUndone[1] == 'movedComponent':
                    if actionUndone[0].name == 'voltmeter':
                        for key in actionUndone[0].voltWires:
                            IDSprites.remove(actionUndone[0].voltWires[key])
                            allSprites.remove(actionUndone[0].voltWires[key])
                    undoneSprite.undo()
                    for sprite in componentSpriteGroup:
                        if sprite.name == 'voltmeter':
                            if sprite.voltWires['left']:
                                voltConnectedSprite = sprite.voltWires['left'].sprites[1]
                                if voltConnectedSprite == actionUndone[0]:
                                    sprite.voltWires['left'].ends[1] = actionUndone[0].left
                                    sprite.voltWires['right'].ends[1] = actionUndone[0].right
                    circuitGraph.resetVectors()
                #Undo component deletion
                elif actionUndone[1] == 'deletedComponent':
                    allSprites.add(undoneSprite)
                    IDSprites.add(undoneSprite)
                    componentSpriteGroup.add(undoneSprite)
                    circuitGraph.addNode(undoneSprite.ID)
                    for key in undoneSprite.connected:
                        if undoneSprite.connected[key] != None:
                            wire = undoneSprite.connected[key]
                            wire.redoCreation()
                            circuitGraph.addEdge(wire.sprites[0].ID,wire.sprites[1].ID)
                    circuitGraph.circuitTest()
                #Undo wire creation
                elif actionUndone[1] == 'createdWire':
                    circuitGraph.removeEdge(undoneSprite)
                    circuitGraph.circuitTest()
                    if circuitGraph.circuitValid == False:
                        for sprite in componentSpriteGroup:
                            sprite.reset()
                    undoneSprite.undoCreation(None)
                self.action()
    
    #Redo action in stack
    def redo(self):
        #If stack not full
        if self.usedItems < self.maximum and self.undoneItems != 0:
            self.usedItems += 1
            self.undoneItems -= 1
            self.rear += 1
            self.rear = self.rear%self.maximum
            actionRedone = self.stack[self.rear]
            if actionRedone != None:
                redoneSprite = actionRedone[0]
                #Redo component creation
                if actionRedone[1] == 'createdComponent':
                    allSprites.add(redoneSprite)
                    IDSprites.add(redoneSprite)
                    componentSpriteGroup.add(redoneSprite)
                    circuitGraph.addNode(redoneSprite.ID)
                #Redo component movement
                elif actionRedone[1] == 'movedComponent':
                    redoneSprite.redo()
                    for sprite in componentSpriteGroup:
                        if sprite.name == 'voltmeter':
                            if sprite.voltWires['left']:
                                voltConnectedSprite = sprite.voltWires['left'].sprites[1]
                                if voltConnectedSprite == actionRedone[0]:
                                    sprite.voltWires['left'].ends[1] = actionRedone[0].left
                                    sprite.voltWires['right'].ends[1] = actionRedone[0].right
                    circuitGraph.resetVectors()
                #Redo component deletion
                elif actionRedone[1] == 'deletedComponent':
                    connectionReset(redoneSprite)
                    circuitGraph.removeNode(redoneSprite.ID)
                    circuitGraph.circuitValid = circuitGraph.circuitTest()
                    if circuitGraph.circuitValid == False:
                        for component in componentSpriteGroup:
                            if component.name == 'voltmeter':
                                if component.voltWires['left']:
                                    voltConnectedSprite = sprite.voltWires['left'].sprites[1]
                                    if voltConnectedSprite == redoneSprite:                                   
                                        component.pd = 0
                                        IDSprites.remove(component.voltWires['left'])
                                        IDSprites.remove(component.voltWires['right'])
                                        allSprites.remove(component.voltWires['left'])
                                        allSprites.remove(component.voltWires['right'])
                                        component.voltWires = {'left': None, 'right': None}
                            component.reset()
                        for electron in electronSprites:
                            for spriteGroup in allGroups:
                                if spriteGroup != IDTracker:
                                    spriteGroup.remove(electron)
                        circuitGraph.resetVectors()
                    for spriteGroup in allGroups:
                        if spriteGroup != IDTracker:
                            spriteGroup.remove(redoneSprite)
                #Redo wire creation
                elif actionRedone[1] == 'createdWire':
                    redoneSprite.redoCreation()
                    circuitGraph.addEdge(redoneSprite.sprites[0].ID,redoneSprite.sprites[1].ID)
            self.action()
    
    #Set component images to red when any action is performed (they become unselected)
    def action(self):
        for sprite in IDSprites:
            if sprite.image == 'red':
                sprite.image = 'base'
                sprite.surf = pygame.image.load(f'graphics/{sprite.name}Base.png')

###Class for circuit graph data structure
class Graph():
    #Constructor
    def __init__(self):
        self.graph = {}
        self.nodeNumber = 0
        self.circuitValid = False
        self.vectorsMade = False
        self.vectorsCycle = []
        self.emfSign = None
        self.currentMultiplier = None
    #Reset graph (reset button pressed)
    def reset(self):
        self.graph = {}
        self.nodeNumber = 0
        self.circuitValid = False
        self.vectorsMade = False
        self.vectorsCycle = []
        self.emfSign = None
        self.currentMultiplier = None
        
    #Add node
    def addNode(self,node):
        if node in self.graph:
            pass
        else:
            self.graph[node] = []
            self.nodeNumber += 1
            #Test if circuit is valid
            self.circuitValid = self.circuitTest()
        self.action()
    
    #Add edge
    def addEdge(self,node1,node2):
        if node1 in self.graph and node2 in self.graph:
            self.graph[node1].append(node2)
            self.graph[node2].append(node1)
            #Test if circuit is valid
            self.circuitValid = self.circuitTest()
        self.action()
    
    #Remove node
    def removeNode(self,node):
        for node2 in self.graph[node]:
            self.graph[node2].remove(node)
        #Test if circuit is valid
        self.circuitValid = self.circuitTest()
        self.graph.pop(node)
        self.nodeNumber -= 1
        self.action()
    
    #Remove edge
    def removeEdge(self,wireSprite):
        spriteIDs = []
        for sprite in wireSprite.sprites:
            spriteIDs.append(sprite.ID)
        for node1 in self.graph:
            if node1 in spriteIDs:
                for node2 in self.graph[node1]:
                    if node2 in spriteIDs:
                        self.graph[node1].remove(node2)
        #Test if circuit is valid
        self.circuitValid = self.circuitTest()
        self.action()

    ########Taken from online source and adjusted *START* ########
    # A recursive function that uses
    # visited[] and parent to detect
    # cycle in subgraph reachable from node v.
    def isCyclicUtil(self, v, visited, parent):
        # Mark the current node as visited
        visited[v] = True
        # Recur for all the vertices
        # adjacent to this node
        for i in self.graph[v]:
            # If the node is not
            # visited then recurse on it
            if visited[i] == False:
                if(self.isCyclicUtil(i, visited, v)):
                    return True
            # If an adjacent node is
            # visited and not parent
            # of current node,
            # then there is a cycle
            elif parent != i:
                return True        
        return False

    # Returns true if the graph
    # contains a cycle, else false.
    def isCyclic(self):
        # Mark all the vertices
        # as not visited
        visited = {}
        for ID in self.graph:
            visited[ID] = False
        # Call the recursive helper
        # function to detect cycle in different
        # DFS trees
        #for i in range(self.nodeNumber):
        for node in self.graph:
            # Don't recur for u if it
            # is already visited
            if visited[node] == False:
                if(self.isCyclicUtil(node, visited, -1)) == True:
                    return True
        return False
    ##### *END OF MODIFIED SOURCED CODE* #####
    
    #Test circuit for conditions
    def circuitTest(self):
        #Test if a cell is present and connected
        cellFound = False
        for sprite in componentSpriteGroup:
            if sprite.name == 'cell' and sprite.ID in self.graph:
                numberOfConnections = 0
                for key in sprite.connected:
                    if sprite.connected[key] != None:
                        numberOfConnections += 1
                if numberOfConnections == 2:
                    cellFound = True
        #Test if the circuit is cycle is a cell is found
        if cellFound == True:
            if self.isCyclic() != True:
                return False
            else:
                return True
        else:
            return False
    
    #Calculate physics whenever an action is performed and the circuit is valid
    def action(self):
        if circuitGraph.circuitValid == True:
            physicsCalc()
    
    #Create vectors for each component and wire and set electron initial positions
    def makeVectors(self):
        #Recursive iterative subprogram to create and store each vector
        def vectorIteration(sprite1,startType,activeSprites,run,skip):
            run += 1
            if sprite1 != activeSprites[0] or run == 1:
                #Find the start and end connectors (left/right) of the wire, and create the sprite vector
                if startType == 'left':
                    endType = 'right'
                    if skip == False:
                        spriteVector = [sprite1,'left','right',Vector(sprite1.left,sprite1.right)]
                    else:
                        spriteVector = None
                else:
                    endType = 'left'
                    if skip == False:
                        spriteVector = [sprite1,'right','left',Vector(sprite1.right,sprite1.left)]
                    else:
                        spriteVector = None
                wire = sprite1.connected[endType]
                sprite2 = None
                for sprite in wire.sprites:
                    if sprite != sprite1:
                        sprite2 = sprite
                skip = False
                #Find the corresponding sprites and connectors for the wire
                sprite1Index = wire.sprites.index(sprite1)
                sprite2Index = wire.sprites.index(sprite2)
                sprite1Type = wire.spriteConnectors[sprite1Index]
                sprite2Type = wire.spriteConnectors[sprite2Index]
                pos1 = wire.ends[sprite1Index]
                pos2 = wire.ends[sprite2Index]
                #Create wire vector
                if sprite1.name == 'junc' and sprite2.name == 'junc':
                    wireVector = ['vector','center','center',Vector(sprite1.currentPosition,sprite2.currentPosition)]
                    skip = True
                elif sprite1.name == 'junc':
                    wireVector = ['vector','center',sprite2Type,Vector(sprite1.currentPosition,pos2)]
                elif sprite2.name == 'junc':
                    wireVector = ['vector',sprite1Type,'center',Vector(pos1,sprite2.currentPosition)]
                    skip = True
                else:
                    wireVector = ['vector',sprite1Type,sprite2Type,Vector(pos1,pos2)]
                #Add created vectors to the vectorsCycle attribute and call a new iteration
                if spriteVector != None:
                    self.vectorsCycle.append(spriteVector)
                self.vectorsCycle.append(wireVector)
                vectorIteration(sprite2,sprite2Type,activeSprites,run,skip)
        
        activeSprites = []
        #Find active sprites
        for sprite in componentSpriteGroup:
            if sprite.ID in self.graph:
                numberOfConnections = 0
                for key in sprite.connected:
                    if sprite.connected[key] != None:
                        numberOfConnections += 1
                if numberOfConnections == 2:
                    activeSprites.append(sprite)
        #Initial iteration call
        vectorIteration(activeSprites[0],'left',activeSprites,0,False)
        self.vectorsMade = True
        #Find the total magnitude of each vector
        self.totalMag = 0
        for item in self.vectorsCycle:
            self.totalMag += item[3].mag
        #Find the number of electrons to create
        self.electronNumber = self.totalMag//50
        #Find the exact spacing each electron should be roughly placed at (~50px)
        self.electronSpacing = self.totalMag/self.electronNumber
        if len(electronSprites) > 0:
            for spriteGroup in allGroups:
                if spriteGroup != IDTracker:
                    for electron in electronSprites:
                        spriteGroup.remove(electron)
        #Temporary position to assign to electrons
        tempPos = (self.vectorsCycle[0][3].pos1)
        vectIndex = 0
        tempPosx = tempPos[0]
        tempPosy = tempPos[1]
        #Iterate though a loop and create each electron
        for i in range(0,int(self.electronNumber)):
            Electron(numberOfSprites(),tempPos,vectIndex)
            xleft = abs(self.vectorsCycle[vectIndex][3].pos2[0] - tempPosx)
            yleft = abs(self.vectorsCycle[vectIndex][3].pos2[1] - tempPosy)
            magLeft = (xleft**2 + yleft**2)**0.5
            if magLeft > self.electronSpacing:
                # +(electronSpacing*moveBy)
                tempPosx += self.electronSpacing * self.vectorsCycle[vectIndex][3].moveBy[0]
                tempPosy += self.electronSpacing * self.vectorsCycle[vectIndex][3].moveBy[1]
            else:
                #Finds how far past the end of a vector the next position will be by
                # finding the magnitude left and takes it from the electronSpacing
                tempPosx = self.vectorsCycle[vectIndex][3].pos2[0]
                tempPosy = self.vectorsCycle[vectIndex][3].pos2[1]
                vectIndex += 1
                if vectIndex == len(self.vectorsCycle):
                    vectIndex = 0
                magOverflow = self.electronSpacing - magLeft
                tempPosx += magOverflow * self.vectorsCycle[vectIndex][3].moveBy[0]
                tempPosy += magOverflow * self.vectorsCycle[vectIndex][3].moveBy[1]
            tempPos = (tempPosx,tempPosy)
    
    #Reset vectors when circuit is broken
    def resetVectors(self):
        self.vectorsMade = False
        self.vectorsCycle = []

###Class for the Unit Graph to show unit relationships
class UnitGraph():
    #Constructor
    def __init__(self,unit1,unit2):
        self.unit1 = unit1
        self.unit2 = unit2
        self.units = {unit1: None,unit2: None}
        self.unitList = [unit1,unit2]
        self.xmax = None
        self.ymax = None
        self.sprite = None
        self.lines = []
        #Assign each unit a value that it is being measured in
        for unit in self.units:
            if unit == 'V':
                self.units[unit] = 'V'
            elif unit == 'I':
                self.units[unit] = 'A'
            elif unit == 'R':
                self.units[unit] = 'Ω'
            elif unit == 'Q':
                self.units[unit] = 'C'
            elif unit == 'LI':
                self.units[unit] = 'Lux'
            elif unit == 'T':
                self.units[unit] = '°C'
        self.axies = {'unit1': [unit1,self.units[unit1]],
                      'unit2': [unit2,self.units[unit2]]}
        #Add to unitGraphGroup to allow access through tkinter and pygame threads
        if len(unitGraphGroup) > 0:
            unitGraphGroup.pop(0)
        unitGraphGroup.append(self)
    
    #Draw N/A for non-applicable relationships for certain components
    def plotNA(self,screen,font):
        surf = font.render('N/A',True,'#ff3344')
        rect = surf.get_rect(center = (874,407))
        screen.blit(surf,rect)
    
    #Draw a linear relationship line
    def plotLinear(self,screen):
        pygame.draw.line(screen,'#ff3333',(787,468),(960,360),width=3)
    
    #Draw the diode I-V relationship line
    def plotDiodeV(self,screen):
        pygame.draw.line(screen,'#ff3333',(787,468),(800,468),width=3)
        pygame.draw.arc(screen,'#ff3333',[775,270,50,200], 4.75,5.25,width=3)
        pygame.draw.line(screen,'#ff3333',(810,458),(865,350),width=3)
    
    #Draw the lamp/thermistor I-V relationship line
    def plotLampThermV(self,screen):
        pygame.draw.arc(screen,'#ff3333',[783,368,437,240], 1.75,3, width=3)
    
    #Draw the ldr/thermistor relationship line for light intensity/temperature
    def plotTempLi(self,screen):
        pygame.draw.arc(screen,'#ff3333',[795,202,300,260], 3.25,4.75, width=3)

###Class for electrons
class Electron(pygame.sprite.Sprite):
    #Constructor
    def __init__(self,ID,initialPos,vectorIndex):
        pygame.sprite.Sprite.__init__(self)
        self.name = 'electron'
        self.ID = ID
        self.currentPos = initialPos
        self.image = 'blue'
        self.surf = pygame.image.load('graphics/electron.png')
        self.rect = self.surf.get_rect(center = initialPos)
        self.shown = False
        #Current vector in the graph's stored vectors that electron is following
        self.vectorIndex = vectorIndex
        IDSprites.add(self)
        electronSprites.add(self)
        allSprites.add(self)
        IDTracker.add(self)
    
    #Toggle whether the electron is visible on the screen
    def toggleShow(self):
        if self.shown == False:
            self.shown = True
        else:
            self.shown = False

###Class for vectors
class Vector():
    #Constructor
    def __init__(self,pos1,pos2):
        self.pos1 = pos1
        self.pos2 = pos2
        self.xdiff = pos2[0]-pos1[0]
        self.ydiff = pos2[1]-pos1[1]
        #Total translation vector
        self.vect = [self.xdiff,self.ydiff]
        self.mag = (self.xdiff**2 + self.ydiff**2)**0.5
        #Relative translation vector for small fraction of the total magnitude
        self.moveBy = [(self.xdiff/self.mag),(self.ydiff/self.mag)]
        if self.xdiff == 0:
            #If x=0, set infinite gradient
            if self.ydiff != 0:
                self.gradient = 'inf'
                self.xchange = 0
                self.ychange = self.ydiff
        else:
            #If x!=0 and y!=0, set normal gradient
            if self.ydiff != 0:
                self.gradient = self.ydiff/self.xdiff
                self.xchange = self.gradient
                self.ychange = 1
            #If x!=0 and y=0, set gradient to 0
            else:
                self.gradient = 0
                self.xchange = self.xdiff
                self.ychange = 0
###Subprogram to find the nearest connector to the mouse
def findNearestConnector(wireOrigin):
    #Finds and returns the magnitude of the line between the mouse pointer
    # and a connector, given that it is less than 75px
    def getMagnitude(pos1,pos2):
        magnitude = ((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)**0.5
        if magnitude <= 75:
            return magnitude
        else:
            return None
    inRangeMagnitude = []
    for sprite in componentSpriteGroup:
        if sprite.name != 'voltmeter':
            #If sprite is not picked up and is not the same sprite the wire was started from
            if sprite.pickupStatus == False and sprite != wireOrigin:
                left = sprite.left
                right = sprite.right
                top = sprite.top
                bottom = sprite.bottom
                leftDist = getMagnitude(pygame.mouse.get_pos(),left)
                rightDist = getMagnitude(pygame.mouse.get_pos(),right)
                topDist = getMagnitude(pygame.mouse.get_pos(),top)
                bottomDist = getMagnitude(pygame.mouse.get_pos(),bottom)
                #Checks the connector is not already connected
                if leftDist != None and sprite.connected['left'] == None:
                    inRangeMagnitude.append([sprite,'left',leftDist])
                if rightDist != None and sprite.connected['right'] == None:
                    inRangeMagnitude.append([sprite,'right',rightDist])
                if topDist != None and sprite.connected['top'] == None:
                    inRangeMagnitude.append([sprite,'top',topDist])
                if bottomDist != None and sprite.connected['bottom'] == None:
                    #Add any connectors found less than 75px away to a list
                    inRangeMagnitude.append([sprite,'bottom',bottomDist])
    #Iterate through connectors found to find the shortest distance
    if len(inRangeMagnitude) > 0:
        lowestFound = 100000000
        for item in inRangeMagnitude:
            if item[2] < lowestFound:
                lowestFound = item[2]
                lowestVector = item
        #If lowest vector is not the same point the wire origionated from, add the proxCircle to be blitted
        if proxCircle not in allSprites and lowestVector[0] != wireOrigin:
            allSprites.add(proxCircle)
        return lowestVector
    #If no connectors are in range remove the proxCircle from the screen
    else:
        if proxCircle in allSprites:
            allSprites.remove(proxCircle)
            proxCircle.pos = (0,0)
        return None

###Subprogram for reseting a component's connections
def connectionReset(sprite):
    #Check if any wires are connected to a sprite, and if so, set them to None.
    for key in sprite.connected:
        if sprite.connected[key] != None:
            wire = sprite.connected[key]
            for wireSprite in wire.sprites:
                if wireSprite != sprite:
                    for otherKey in wireSprite.connected:
                        if wireSprite.connected[otherKey] != None:
                            if wireSprite.connected[otherKey] == wire:
                                wireSprite.connected[otherKey] = None
            #Undo creation of the wire to delete it from the screen and reset its values
            wire.undoCreation(sprite)
            
###Subprogram to assign each sprite an ID
def numberOfSprites():
    #Gets the number of sprites which have existed during run time and assigns the sprite
    # the next number as an ID
    newID = len(IDTracker)
    newID += 1
    return newID

###Subprogram for calculating physics circuit values
def physicsCalc():
    #Only calculate if circuit is valid
    if circuitGraph.circuitValid == True:
        activeSprites = []
        current = 0
        emf = 0
        for sprite in componentSpriteGroup:
            if sprite.ID in circuitGraph.graph:
                numberOfConnections = 0
                for key in sprite.connected:
                    if sprite.connected[key] != None:
                        numberOfConnections += 1
                if numberOfConnections == 2:
                    activeSprites.append(sprite)
        #Find total emf before calculating current and voltage, and find the resistance
        # of any LDRs and thermistors
        for sprite in activeSprites:
            #Add to emf if cell to give total emf
            if sprite.name == 'cell':
                emf += sprite.emf
            #Calculate resistance of thermistor given its temperature
            elif sprite.name == 'thermistor':
                e = math.exp(1)
                sprite.resistance = (sprite.resistance)*(e**(3000*((1/(sprite.temp+273)) - (1/(sprite.prevTemp+273)))))
            #Calculate resistance of ldr given its light intensity
            elif sprite.name == 'ldr':
                e = math.exp(1)
                sprite.resistance = (sprite.resistance)*(e**(5000*((1/sprite.LI) - (1/sprite.prevLI))))
        #Find the emf direction multiplier to determine the direction of electrons
        if -0.01 < emf < 0.01:
            circuitGraph.emfSign = 0
        elif emf >= 0.01:
            circuitGraph.emfSign = 1
        elif emf <= -0.01:
            circuitGraph.emfSign = -1
        #Find the total resistance of any circuit components
        totalRes = 0
        for comp in activeSprites:
            if 'resistance' in comp.allAttributes():
                if comp.resistance:
                    totalRes += comp.resistance
        if totalRes != 0:
            #Calculate current with I=V/R
            current = emf/totalRes
            nonPwrSprites = ['ammeter','voltmeter','junc']
            for sprite in activeSprites:
                sprite.current = current            
                if 'resistance' in sprite.allAttributes():
                    #If cell has an internal resistance, divide emf into an equal fraction of its resistance
                    # compared to the total resistance to give the "lost volts" in the cell
                    if sprite.name == 'cell':
                        sprite.lostV = emf*(sprite.resistance/totalRes)
                    #Calulate the voltage for each component by dividing the emf into an equal fraction
                    # of its resistance compared to the total resistance
                    else:
                        sprite.pd = emf*(sprite.resistance/totalRes)
                #Calculate power of applicable components using P=IV
                if sprite.name not in nonPwrSprites:
                    if sprite.name == 'cell':
                        sprite.power = current*sprite.emf
                    else:
                        sprite.power = current*sprite.pd
                #If the diode voltage is below the threshhold (minimum) voltage, set current to 0
                if sprite.name == 'diode':
                    if sprite.pd < sprite.minThresh:
                        current = 0
                        for sprite in activeSprites:
                            sprite.current = 0
            #Calculate the currentMultiplier for speed of moving electrons
            if abs(current*0.5) <= 30/9:
                circuitGraph.currentMultiplier = abs(current*0.5)
            else:
                circuitGraph.currentMultiplier = abs(30/9)
            #Set voltage of any connected voltmeters to their corresponding component
            for sprite in componentSpriteGroup:
                if sprite.name == 'voltmeter':
                    if sprite.voltWires['left']:
                        voltConnectedSprite = sprite.voltWires['left'].sprites[1]
                        if voltConnectedSprite.name == 'cell':
                            sprite.pd = voltConnectedSprite.emf
                        else:
                            sprite.pd = voltConnectedSprite.pd
        #If circuit has 0 resistance, set current to infinity and other circuit values to 0.
        else:
            current = math.inf
            circuitGraph.currentMultiplier = abs(30/9)
            for sprite in activeSprites:
                sprite.current = math.inf
                sprite.pd = 0
                sprite.power = 0
            for sprite in componentSpriteGroup:
                if sprite.name == 'voltmeter':
                    sprite.pd = 0

###Subprogram for drawing the selected component's circuit values
def drawStatsText(screen,selectedSprite,font):
    if selectedSprite:
        if selectedSprite.image == 'red' and selectedSprite in allSprites:
            atts = selectedSprite.allAttributes()
            showableTexts = ['current','pd','emf','resistance','temp','LI','minThresh','power','lostV']
            if selectedSprite.name == 'voltmeter' and 'current' in atts:
                del(atts['current'])
            yPos = 60
            #Set text values to blit and their unit's symbol
            for textName in showableTexts:
                if textName in atts:
                    if textName == 'emf':
                        text = 'e.m.f'
                        symbol = 'V'
                    elif textName == 'pd':
                        text = 'Voltage'
                        symbol = 'V'
                    elif textName == 'current':
                        text = 'Current'
                        symbol = 'A'
                    elif textName == 'resistance':
                        text = 'Resistance'
                        symbol = 'Ω'
                    elif textName == 'temp':
                        text = 'Temperature'
                        symbol = '°C'
                    elif textName == 'LI':
                        text = 'Light Int'
                        symbol = ' Lux'
                    elif textName == 'minThresh':
                        text = 'Min Voltage'
                        symbol = 'V'
                    elif textName == 'power':
                        text = 'Power'
                        symbol = 'W'
                    elif textName == 'lostV':
                        text = '"Lost Volts"'
                        symbol = 'V'
                    #Set the value of the attribute
                    if atts[textName]:
                        value = round(atts[textName], 2)
                    else:
                        value = 0
                    #Show text and draw a red box around the components customisable value
                    surf = font.render(f'{text}: {value}{symbol}',True,'#333333')
                    rect = surf.get_rect(midleft = (760,yPos))
                    screen.blit(surf,rect)
                    if 'customVal' in selectedSprite.allAttributes():
                        if textName == selectedSprite.customVal:
                            pygame.draw.rect(screen,'#ff2222',(755,yPos-15,242,32),width=1)
                    #Add 30px to the y position text is shown at ready for the next iteration 
                    yPos += 30

###Subprogram for resetting the circuit
def resetCircuitBoard():
    #Clear sprite groups
    for sprite in allSprites:
        allSprites.remove(sprite)
        if sprite in IDSprites:
            IDSprites.remove(sprite)
        if sprite in componentSpriteGroup:              
            componentSpriteGroup.remove(sprite)
    #Reset Undo/Redo system
    actions.reset()
    #Reset circuit graph
    circuitGraph.reset()

#Set up actions stack
actions = Cstack('actions',10)
#Set up graph data structure
circuitGraph = Graph()
#Set up component circuit values/attributes and set the 
# initial customisable value for the component type
cellAttributes = {'current': None,
                  'emf': 5,
                  'resistance': 0,
                  'power': None,
                  'lostV': 0,
                  'customVal': 'emf'}
lampAttributes = {'current': None,
                  'pd': None,
                  'resistance': 5,
                  'power': None,
                  'customVal': 'resistance'}
resistorAttributes = {'current': None,
                      'pd': None,
                      'resistance': 10,
                      'power': None,
                      'customVal': 'resistance'}
juncAttributes = {'current': None}
ammeterAttributes = {'current': None,}
voltmeterAttributes = {'pd': None}
thermistorAttributes = {'current': None,
                        'pd': None,
                        'resistance': 10,
                        'temp': 21,
                        'power': None,
                        'customVal': 'temp'}
ldrAttributes = {'current': None,
                 'pd': None,
                 'resistance': 10,
                 'LI': 500,
                 'power': None,
                 'customVal': 'LI'}
diodeAttributes = {'current': None,
                   'pd': None,
                   'resistance': 10,
                   'minThresh': 1,
                   'power': None,
                   'customVal': 'resistance'}
#Unit Graph Group (stores unit graph to be access by both the tkinter and pygame threads
unitGraphGroup = []
#Set up sprite groups
componentSpriteGroup = pygame.sprite.Group()
allSprites = pygame.sprite.Group()
IDSprites = pygame.sprite.Group()
electronSprites = pygame.sprite.Group()
IDTracker = pygame.sprite.Group()
allGroups = [allSprites,IDSprites,componentSpriteGroup,electronSprites,IDTracker]
#Set up constant images
proxCircle = ProxCircle('proxCircle',0,(0,0))
#Set selectedSprite to None to allow access between both the tkinter and pygame threads
selectedSprite = None

#####Tkinter Thread
def tkBoxRun():
    ###Class for the tkinter window
    class tkWindow():
        #Constructor
        def __init__(self,windowName):
            self.window = None
            self.windowName = windowName
            self.root = tk.Tk()
            self.root.title('Components')
            self.embed = Frame(self.root, width=640, height=480)
            os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
            os.environ['SDL_VIDEODRIVER'] = 'windib'
            if self.windowName == 'boxWin':
                self.root.geometry('275x600+110+120')
                #Set component images
                self.imageCell = PhotoImage(file='graphics/cellIcon.png')
                self.imageLamp = PhotoImage(file='graphics/lampIcon.png')
                self.imageResistor = PhotoImage(file='graphics/resistorIcon.png')
                self.imageJunc = PhotoImage(file='graphics/juncIcon.png')
                self.imageAmmeter = PhotoImage(file='graphics/ammeterIcon.png')
                self.imageVoltmeter = PhotoImage(file='graphics/voltmeterIcon.png')
                self.imageThermistor = PhotoImage(file='graphics/thermistorIcon.png')
                self.imageLDR = PhotoImage(file='graphics/ldrIcon.png')
                self.imageDiode = PhotoImage(file='graphics/diodeIcon.png')
                self.borderColor = tk.Frame(self.root,background='red')
                #Create and set component buttons into a grid
                self.cellButton = tk.Button(self.root, text='Cell', image=self.imageCell, command=self.cellCommand,relief=GROOVE)
                self.cellButton.grid(row=0,column=0,padx=2.5)
                self.lampButton = tk.Button(self.root, text='Lamp', image=self.imageLamp, command=self.lampCommand,relief=GROOVE)
                self.lampButton.grid(row=1,column=0,padx=2.5)
                self.resistorButton = tk.Button(self.root, text='Resistor', image=self.imageResistor, command=self.resistorCommand,relief=RIDGE)
                self.resistorButton.grid(row=0,column=2,padx=2.5)
                self.juncButton = tk.Button(self.root, text='Junc', image=self.imageJunc, command=self.juncCommand,relief=RIDGE)
                self.juncButton.grid(row=0,column=1,padx=2.5)
                self.ammeterButton = tk.Button(self.root, text='Ammeter', image=self.imageAmmeter, command=self.ammeterCommand,relief=RIDGE)
                self.ammeterButton.grid(row=1,column=1,padx=2.5)
                self.voltmeterButton = tk.Button(self.root, text='Voltmeter', image=self.imageVoltmeter, command=self.voltmeterCommand,relief=RIDGE)
                self.voltmeterButton.grid(row=1,column=2,padx=2.5)
                self.thermistorButton = tk.Button(self.root, text='Thermistor', image=self.imageThermistor, command=self.thermistorCommand,relief=RIDGE)
                self.thermistorButton.grid(row=2,column=0,padx=2.5)
                self.ldrButton = tk.Button(self.root, text='LDR', image=self.imageLDR, command=self.ldrCommand,relief=RIDGE)
                self.ldrButton.grid(row=2,column=1,padx=2.5)
                self.diodeButton = tk.Button(self.root, text='Diode', image=self.imageDiode, command=self.diodeCommand,relief=RIDGE)
                self.diodeButton.grid(row=2,column=2,padx=2.5)
                #Set Unit Graph images
                self.imageiv = PhotoImage(file='graphics/ivIcon.png')
                self.imagert = PhotoImage(file='graphics/rtIcon.png')
                self.imagerli = PhotoImage(file='graphics/rliIcon.png')
                #Create and set Unit Graph buttons into the grid
                self.ivButton = tk.Button(self.root, text='I/V', image=self.imageiv, command=self.ivCommand,relief=GROOVE)
                self.ivButton.grid(row=6,column=0,padx=2.5,pady=50)
                self.rliButton = tk.Button(self.root, text='R/LI', image=self.imagerli, command=self.rliCommand,relief=GROOVE)
                self.rliButton.grid(row=6,column=1,padx=2.5,pady=50)
                self.rtButton = tk.Button(self.root, text='R/T', image=self.imagert, command=self.rtCommand,relief=GROOVE)
                self.rtButton.grid(row=6,column=2,padx=2.5,pady=50)
                #Set Reset button image and create button, setting it into the grid
                self.imageReset = PhotoImage(file='graphics/resetIcon.png')
                self.resetButton = tk.Button(self.root, text='Reset', image=self.imageReset, command=self.resetCommand,relief=GROOVE)
                self.resetButton.grid(row=7,column=0,padx=2.5,pady=0)
            self.root.mainloop()
            
        def addLastAction(self,sprite):
            #Add component creation to actions stack
            lastAction = [sprite,'createdComponent']
            actions.add(lastAction)
            #Add new component to the graph data structure
            circuitGraph.addNode(sprite.ID)
        ##Button command methods for creating a each component
        def cellCommand(self):
            newCell = Component('cell',numberOfSprites(),cellAttributes,(500,300))
            self.addLastAction(newCell)
        def lampCommand(self):
            newLamp = Component('lamp',numberOfSprites(),lampAttributes,(500,300))
            self.addLastAction(newLamp)
        def resistorCommand(self):
            newResistor = Component('resistor',numberOfSprites(),resistorAttributes,(500,300))
            self.addLastAction(newResistor)
        def juncCommand(self):
            newJunc = Component('junc',numberOfSprites(),juncAttributes,(500,300))
            self.addLastAction(newJunc)
        def ammeterCommand(self):
            newammeter = Component('ammeter',numberOfSprites(),ammeterAttributes,(500,300))
            self.addLastAction(newammeter)
        def voltmeterCommand(self):
            newvoltmeter = Component('voltmeter',numberOfSprites(),voltmeterAttributes,(500,300))
            self.addLastAction(newvoltmeter)
        def thermistorCommand(self):
            newThermistor = Component('thermistor',numberOfSprites(),thermistorAttributes,(500,300))
            self.addLastAction(newThermistor)
        def ldrCommand(self):
            newLDR = Component('ldr',numberOfSprites(),ldrAttributes,(500,300))
            self.addLastAction(newLDR)
        def diodeCommand(self):
            newDiode = Component('diode',numberOfSprites(),diodeAttributes,(500,300))
            self.addLastAction(newDiode)
        #Reset button command method for resetting the circuit
        def resetCommand(self):
            resetCircuitBoard()
        ##Unit Graph button command methods for creating and setting a new unit graph
        def ivCommand(self):
            UnitGraph('I', 'V')
        def rtCommand(self):
            UnitGraph('R', 'T')
        def rliCommand(self):
            UnitGraph('R', 'LI')
    tkWindow('boxWin')
    root = tk.Tk()

#####Pygame thread
def pygameRun():
    ##Setup pygame 
    pygame.init()
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (400,150)
    screen = pygame.display.set_mode((1000,600))
    pygame.display.set_caption('Circuit Board')
    pygame.display.set_icon(pygame.image.load('graphics/bolt.png'))
    clock = pygame.time.Clock()
    ##Set label surfaces and rectangles
    font = pygame.font.SysFont('malgungothic',20)
    fontsmall = pygame.font.SysFont('malgungothic',18)
    fontHuge = pygame.font.SysFont('malgungothic',40)
    statsLabelSurf1 = fontsmall.render('Shows stats of selected component',True,'#bb3333')
    statsLabelRect1 = statsLabelSurf1.get_rect(midleft = (450,40))
    statsLabelSurf2 = fontsmall.render('(right clicked) ------------------>',True,'#bb3333')
    statsLabelRect2 = statsLabelSurf2.get_rect(midleft = (450,70))
    boxLabelSurf1 = fontsmall.render('Click component to add it to',True,'#bb3333')
    boxLabelRect1 = boxLabelSurf1.get_rect(midright = (238,40))
    boxLabelSurf2 = fontsmall.render('<--------------- the board',True,'#bb3333')
    boxLabelRect2 = boxLabelSurf2.get_rect(midright = (238,70))
    graphLabelSurf1 = fontsmall.render('Shows graph of selected type for selected',True,'#bb3333')
    graphLabelRect1 = graphLabelSurf1.get_rect(midleft = (385,390))
    graphLabelSurf2 = fontsmall.render('component or whole circuit ------------>',True,'#bb3333')
    graphLabelRect2 = graphLabelSurf2.get_rect(midleft = (385,420))
    gboxLabelSurf1 = fontsmall.render('Click on graph type to show the',True,'#bb3333')
    gboxLabelRect1 = gboxLabelSurf1.get_rect(midright = (265,330))
    gboxLabelSurf2 = fontsmall.render('<------------------ graph box',True,'#bb3333')
    gboxLabelRect2 = gboxLabelSurf2.get_rect(midright = (265,360))
    resetLabelSurf1 = fontsmall.render('Click reset to clear the circuit board',True,'#bb3333')
    resetLabelRect1 = resetLabelSurf1.get_rect(midright = (293,460))
    resetLabelSurf2 = fontsmall.render('<------------- (cannot be undone)',True,'#bb3333')
    resetLabelRect2 = resetLabelSurf2.get_rect(midright = (293,490))
    incLabelSurf1 = fontsmall.render('Amount to increment selected quantity',True,'#bb3333')
    incLabelRect1 = incLabelSurf1.get_rect(midleft = (417,250))
    incLabelSurf2 = fontsmall.render('by for selected sprite ----------------->',True,'#bb3333')
    incLabelRect2 = incLabelSurf2.get_rect(midleft = (417,280))
    toggleLabelsSurf = font.render('Toggle Labels: 1,',True,'#bb3333')
    toggleLabelsRect = toggleLabelsSurf.get_rect(midleft = (5,580))
    toggleElectronsSurf = font.render('Toggle Electrons: 2,',True,'#3333bb')
    toggleElectronsRect = toggleElectronsSurf.get_rect(midleft = (165,580))
    toggleControlsSurf = font.render('Toggle Controls: 3',True,'#800080')
    toggleControlsRect = toggleControlsSurf.get_rect(midleft = (348,580))
    #Set Stats Box title text
    statsTxtSurf = font.render('Selected Component:',True,'#222222')
    statsTxtRect = statsTxtSurf.get_rect(midleft = (760,20))
    ##Set Controls text surfaces and rectangles
    controlsSurf = font.render('Controls:',True,'#800080')
    controlsRect = controlsSurf.get_rect(midleft = (760,20))
    escControlSurf = font.render('Esc: Close Program',True,'#800080')
    escControlRect = escControlSurf.get_rect(midleft = (760,60))
    lClickControlSurf = font.render('L Click: Drag Component',True,'#800080')
    lClickControlRect = lClickControlSurf.get_rect(midleft = (760,90))
    rClickControlSurf = font.render('R Click: Select/Drag wire',True,'#800080')
    rClickControlRect = rClickControlSurf.get_rect(midleft = (760,120))
    delControlSurf = font.render('Delete: Del Selected',True,'#800080')
    delControlRect = delControlSurf.get_rect(midleft = (760,150))
    sControlSurf = font.render('S: Save Screenshot',True,'#800080')
    sControlRect = sControlSurf.get_rect(midleft = (760,180))
    undoControlSurf = font.render('Backspace: Undo',True,'#800080')
    undoControlRect = undoControlSurf.get_rect(midleft = (760,210))
    redoControlSurf = font.render('Tab: Redo',True,'#800080')
    redoControlRect = redoControlSurf.get_rect(midleft = (760,240))
    upControlSurf = font.render('↑ Incr Custom Value',True,'#800080')
    upControlRect = upControlSurf.get_rect(midleft = (760,270))
    downControlSurf = font.render('↓ Decr Custom Value',True,'#800080')
    downControlRect = downControlSurf.get_rect(midleft = (760,300))
    stepControlSurf = font.render('← → Inc/Dec Step',True,'#800080')
    stepControlRect = stepControlSurf.get_rect(midleft = (760,330))
    cControlSurf = font.render('C: Change Custom Value',True,'#800080')
    cControlRect = cControlSurf.get_rect(midleft = (760,360))
    ##Set initial predetermined variables
    pickup = False
    wireOriginSprite = None
    makingWire = False
    wireOriginConnector = None
    rightClickSinglePress = False
    selectedSprite = None
    customOrder = 1
    leftWire = None
    rightWire = None
    unit1 = None
    unit2 = None
    symbol1 = None
    symbol2 = None
    labelsOn = False
    controlsOn = False
    screenshotData = []
    screenshotTaken = False
    screenshotIteration = 0
    saveScreenshot = False
    #Set current screenshot number by loading the screenshotData file containing the number of past screenshots
    with open('screenshots/screenshotData.txt', 'r') as file:
        for line in file:
            screenshotData.append(line)
    screenshotNumber = int(screenshotData[0])
    ###Event loop
    while True:
        if selectedSprite:
            if len(allSprites) == 0:
                selectedSprite = None
        screen.fill('#777777')
        ##Check for events and key presses
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                #If the 'c' key is pressed, change the customisable value of the selected sprite if applicable
                if event.key == pygame.K_c:
                    if selectedSprite != None:
                        if selectedSprite.name == 'cell':
                            if selectedSprite.customVal == 'emf':
                                selectedSprite.customVal = 'resistance'
                            else:
                                selectedSprite.customVal = 'emf'
                        elif selectedSprite.name == 'diode':
                            if selectedSprite.customVal == 'minThresh':
                                selectedSprite.customVal = 'resistance'
                            else:
                                selectedSprite.customVal = 'minThresh'                
                ##If the backspace key is pressed, undo the last action
                if event.key == pygame.K_BACKSPACE:
                    actions.undo()
                    selectedSprite = None
                ##If the tab key is pressed, redo the last undone action
                if event.key == pygame.K_TAB:
                    actions.redo()
                    selectedSprite = None
                ##If the delete key is pressed, delete the selected sprite
                if event.key == pygame.K_DELETE:
                    for sprite in IDSprites:
                        if sprite in componentSpriteGroup:
                            if sprite.rightClicked == True:
                                #If a voltmeter, remove the wires connecting it to any components
                                if sprite.name == 'voltmeter':
                                    if sprite.voltWires['left']:
                                        sprite.pd = 0
                                        IDSprites.remove(sprite.voltWires['left'])
                                        IDSprites.remove(sprite.voltWires['right'])
                                        allSprites.remove(sprite.voltWires['left'])
                                        allSprites.remove(sprite.voltWires['right'])
                                        sprite.voltWires = {'left': None, 'right': None}
                                sprite.rightClicked = False
                                #Add component deletion to actions stack
                                actions.add([sprite,'deletedComponent'])
                                #Reset deleted components wires
                                connectionReset(sprite)
                                #Remove component from graph data structure
                                circuitGraph.removeNode(sprite.ID)
                                #Test if circuit is still valid
                                circuitGraph.circuitValid = circuitGraph.circuitTest()
                                if circuitGraph.circuitValid == False:
                                    #Reset all components if circuit is broken
                                    for component in componentSpriteGroup:
                                        #If component is voltmeter reset its connecting wires
                                        if component.name == 'voltmeter':
                                            if component.voltWires['left']:
                                                voltConnectedSprite = component.voltWires['left'].sprites[1]
                                                if voltConnectedSprite == sprite:
                                                    component.pd = 0
                                                    IDSprites.remove(component.voltWires['left'])
                                                    IDSprites.remove(component.voltWires['right'])
                                                    allSprites.remove(component.voltWires['left'])
                                                    allSprites.remove(component.voltWires['right'])
                                                    component.voltWires = {'left': None, 'right': None}
                                        component.reset()
                                    #Delete all electrons is circuit is broken
                                    for electron in electronSprites:
                                        for spriteGroup in allGroups:
                                            if spriteGroup != IDTracker:
                                                spriteGroup.remove(electron)
                                    circuitGraph.resetVectors()
                                #Remove deleted component from sprite groups
                                for spriteGroup in allGroups:
                                    if spriteGroup != IDTracker:
                                        spriteGroup.remove(sprite)
                    selectedSprite = None
                #If left arrow key is pressed, change the increment step by a factor of 1/10
                if event.key == pygame.K_LEFT:
                    customOrder /= 10
                    #Loop back to 1 if nessessary
                    if customOrder < 0.01:
                        customOrder = 1
                #If right arrow key is pressed, change the increment step by a factor of 10
                if event.key == pygame.K_RIGHT:
                    customOrder *= 10
                    #Loop back to 0.01 if nessessary
                    if customOrder > 1:
                        customOrder = 0.01
                #If up arrow key is pressed, increase the customisable value for the selected component by the increment step
                if event.key == pygame.K_UP:
                    if selectedSprite != None:
                        if selectedSprite.name != 'voltmeter' and selectedSprite.name != 'ammeter' and selectedSprite.name != 'junc':
                            #Use copy to prevent variable automatic updates for certain values
                            prevOrder = copy.copy(customOrder)
                            if selectedSprite.customVal == 'temp':
                                selectedSprite.prevTemp = copy.copy(selectedSprite.temp)
                            elif selectedSprite.customVal == 'LI':
                                selectedSprite.prevLI = copy.copy(selectedSprite.LI)
                                customOrder *= 10
                            #Add to customisable value
                            vars(selectedSprite)[selectedSprite.customVal] += customOrder
                            customOrder = prevOrder
                            ##If component is an LDR/thermistor, calculate its resistance as the circuit does not need to be active for this
                            if selectedSprite.name == 'thermistor':
                                e = math.exp(1)
                                try:
                                    selectedSprite.resistance = (selectedSprite.resistance)*(e**(3000*((1/(selectedSprite.temp+273)) - (1/(selectedSprite.prevTemp+273)))))
                                except:
                                    pass
                            elif selectedSprite.name == 'ldr':
                                e = math.exp(1)
                                try:
                                    selectedSprite.resistance = (selectedSprite.resistance)*(e**(5000*((1/selectedSprite.LI) - (1/selectedSprite.prevLI))))
                                except:
                                    pass
                            #Re-calculate physics with updated values if circuit is complete
                            if circuitGraph.circuitValid == True:
                                physicsCalc()
                #If down arrow key is pressed, decrease the customisable value for the selected component by the increment step
                if event.key == pygame.K_DOWN:
                    if selectedSprite != None:
                        if selectedSprite.name != 'voltmeter' and selectedSprite.name != 'ammeter' and selectedSprite.name != 'junc':
                            prevOrder = copy.copy(customOrder)
                            changeVal = selectedSprite.customVal
                            if changeVal == 'temp':
                                selectedSprite.prevTemp = copy.copy(selectedSprite.temp)
                            elif changeVal == 'LI':
                                selectedSprite.prevLI = copy.copy(selectedSprite.LI)
                                customOrder *= 10
                            vars(selectedSprite)[changeVal] -= customOrder
                            customOrder = prevOrder
                            #In addition to the up arrow functionalites for decreasing values,
                            # if temperature falls below -273, do not change it and
                            # then if any custom values other than emf fall below 0, do not change it
                            if changeVal == 'temp':
                                if selectedSprite.temp < -273:
                                    selectedSprite.temp = -273
                            elif changeVal != 'emf' and vars(selectedSprite)[changeVal] < 0:
                                vars(selectedSprite)[changeVal] = 0
                            if selectedSprite.name == 'thermistor':
                                e = math.exp(1)
                                try:
                                    selectedSprite.resistance = (selectedSprite.resistance)*(e**(3000*((1/(selectedSprite.temp+273)) - (1/(selectedSprite.prevTemp+273)))))
                                except:
                                    pass
                            elif selectedSprite.name == 'ldr':
                                e = math.exp(1)
                                try:
                                    selectedSprite.resistance = (selectedSprite.resistance)*(e**(5000*((1/selectedSprite.LI) - (1/selectedSprite.prevLI))))
                                except:
                                    pass
                            if circuitGraph.circuitValid == True:
                                physicsCalc()
                #If '1' key is pressed, toggle labels to show and stop showing any controls               
                if event.key == pygame.K_1:
                    if labelsOn == True:
                        labelsOn = False
                    else:
                        labelsOn = True
                        controlsOn = False
                #If '2' key is pressed, toggle electrons to show
                if event.key == pygame.K_2:
                    if pickup == False:
                        for electron in electronSprites:
                            if electron.shown == False:
                                electron.shown = True
                            else:
                                electron.shown = False
                #If '3' key is pressed, toggle controls to show and stop showing any labels
                if event.key == pygame.K_3:
                    if controlsOn == True:
                        controlsOn = False
                    else:
                        controlsOn = True
                        labelsOn = False
                #If escape is pressed, close pygame
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                #If the 's' key is pressed set screenshot values to take screenshot further into the event loop
                if event.key == pygame.K_s:
                    saveScreenshot = True
                    screenshotTaken = True
                    
        ###Check is mouse buttons are pressed
        #Check if left or middle click is pressed
        if pygame.mouse.get_pressed()[0] == True:
            #Check if a component is already picked up
            if pickup == False:
                sprite = None
                spriteList = []
                #Check that user is not dragging a wire
                if makingWire == False:
                    for sprite in componentSpriteGroup:
                        spriteList.append(sprite)
                    for sprite in reversed(spriteList):
                        #If mouse is on a component and not the proxCircle, pickup component and set it to follow the mouse
                        if sprite.rect.collidepoint(pygame.mouse.get_pos()):
                            sprite.pickupStatus = True
                            pickup = True
                            #Make any visible electrons invisible
                            for electron in electronSprites:
                                if electron.shown == True:
                                    electron.shown = False
                            #If the component being moved is a voltmeter, remove any existing wires connecting it to a component
                            if sprite.name == 'voltmeter':
                                for key in sprite.voltWires:
                                    IDSprites.remove(sprite.voltWires[key])
                                    allSprites.remove(sprite.voltWires[key])
                                sprite.voltWires = {'left': None,'right': None}
                            #Create next component movement action to be added to the stack
                            lastAction = [sprite,'movedComponent']
                            #Save the sprites position to an action file to be loaded for undo/redo
                            sprite.save('new')
                            sprite.rect = sprite.surf.get_rect(center = pygame.mouse.get_pos())
                            break
            else:
                #If component is being moved, set its center position to the mouse pointer
                for sprite in componentSpriteGroup:
                    if sprite.pickupStatus == True:
                        sprite.rect = sprite.surf.get_rect(center = pygame.mouse.get_pos())
                        sprite.currentPosition = pygame.mouse.get_pos()
                        #If component is a voltmeter and within 75px of another component, create wires between the voltmeter and component
                        if sprite.name == 'voltmeter':
                            if nearestPoint:
                                if nearestPoint[0].name != 'ammeter':
                                    #If wires do not exist between the voltmeter and other component, create them
                                    if not(sprite.voltWires['left'] and sprite.voltWires['right']):
                                        leftWire = Wire(numberOfSprites(),sprite.left,nearestPoint[0].left,'voltLeft')
                                        rightWire = Wire(numberOfSprites(),sprite.right,nearestPoint[0].right,'voltRight')
                                        sprite.voltWires = {'left': leftWire,'right': rightWire}
                                        leftWire.sprites = [sprite,nearestPoint[0]]
                                        rightWire.sprites = [sprite,nearestPoint[0]]
                                    else:
                                        #Draw temporary red wires to show where wires will be created when voltmeter is put down
                                        pygame.draw.aaline(screen,'#ff0000',sprite.left,nearestPoint[0].left,2)
                                        pygame.draw.aaline(screen,'#ff0000',sprite.right,nearestPoint[0].right,2)
                                        sprite.voltWires['left'].ends = [sprite.left,nearestPoint[0].left]
                                        sprite.voltWires['right'].ends = [sprite.right,nearestPoint[0].right]
                                        sprite.voltWires['left'].sprites = [sprite,nearestPoint[0]]
                                        sprite.voltWires['right'].sprites = [sprite,nearestPoint[0]]
                                        sprite.voltWires['left'].spriteConnectors = ['left','left']
                                        sprite.voltWires['right'].spriteConnectors = ['right','right']
                            else:
                                #Delete existing voltWires if component is not within 75px
                                sprite.voltWires = {'left': None,'right': None}
                                lw = sprite.voltWires['left']
                                rw = sprite.voltWires['right']
                                if lw and lw in IDSprites:
                                    IDSprites.remove(lw)
                                    allSprites.remove(lw)
                                if rw and rw in IDSprites:
                                    IDSprites.remove(rw)
                                    allSprites.remove(rw)
        #Check if right click is pressed
        elif pygame.mouse.get_pressed()[2] == True:
            #Check that component is not picked up
            if pickup == False:
                sprite = None
                spriteList = []
                #Check that user is not dragging a wire
                if makingWire == False:
                    for sprite in componentSpriteGroup:
                        spriteList.append(sprite)
                    for sprite in reversed(spriteList):
                        #If mouse is on the proxCircle, create and start dragging a wire
                        if sprite.name != 'junc' and proxCircle.rect.collidepoint(pygame.mouse.get_pos()) and circuitGraph.isCyclic() == False:
                            makingWire = True
                            selectedSprite = None
                            wireOriginConnector = nearestPoint[1]
                            wireOriginSprite = nearestPoint[0]
                            newWire = Wire(numberOfSprites(),proxCircle.pos,pygame.mouse.get_pos(),'newWire')
                            break
            #If right click was not pressed in the previous event loop iteration and a wire is not being dragged
            if rightClickSinglePress == False and makingWire == False:
                for sprite in IDSprites:
                    if sprite in componentSpriteGroup:
                        #If mouse is on a component toggle the image to be red or black
                        if sprite.rect.collidepoint(pygame.mouse.get_pos()):
                            if sprite.image == 'base':
                                for redImageSprite in componentSpriteGroup:
                                    if redImageSprite.image == 'red':
                                        redImageSprite.toggleImage()
                                        redImageSprite.rightClicked = False
                                selectedSprite = sprite
                                #If a unit graph is selected set the sprite stored to the selected sprite
                                if len(unitGraphGroup) > 0:
                                    unitGraphGroup[0].sprite = sprite
                                sprite.rightClicked = True
                                sprite.toggleImage()
                            elif sprite.image == 'red':
                                selectedSprite = None
                                sprite.toggleImage()
                                sprite.rightClicked = False
                rightClickSinglePress = True
        #If mouse clicks not pressed
        else:
            #Is component is picked up
            if pickup == True:
                #Deselect any components
                selectedSprite = None
                #Reset circuit vectors and electrons
                circuitGraph.resetVectors()
                #Add last movement to actions stack
                actions.add(lastAction)
            #If wire is being dragged, stop making wire and update the wire end
            if makingWire == True:
                makingWire = False
                newWire.updateEnd(nearestPoint,makingWire,wireOriginSprite,wireOriginConnector)
            #Reset pickup/dragging variables
            pickup = False
            wireOriginSprite = None
            wireOriginConnector = None
            makingWire = False
            rightClickSinglePress = False
            #Re-calculate physics when a voltmeter is connected
            for sprite in componentSpriteGroup:
                if sprite.pickupStatus == True:
                    if sprite.name == 'voltmeter':
                        if sprite.voltWires['left'] and sprite.voltWires['right']:
                            sprite.voltWires['left'].placed = True
                            sprite.voltWires['right'].placed = True
                            physicsCalc()
                    sprite.pickupStatus = False
        ###Draw any shapes and text if applicable
        if labelsOn == True:
            pygame.draw.rect(screen,'#999999',(750,0,600,600))
        pygame.draw.rect(screen,'#000000',(750,0,1200,300),width=3)
        pygame.draw.line(screen,'#000000',(750,40),(1200,40),3)
        #Show increment step with the current set value to increase/decrease by
        if selectedSprite != None:
            if selectedSprite.name == 'ldr':
                incrementOrderSurf = font.render(f'Increment Step: < {str(round(customOrder*10,2))} >',True,'#222222')
            else:
                incrementOrderSurf = font.render(f'Increment Step: < {str(round(customOrder,2))} >',True,'#222222')
        else:
            incrementOrderSurf = font.render(f'Increment Step: < {str(round(customOrder,2))} >',True,'#222222')
        incrementOrderRect = incrementOrderSurf.get_rect(midleft = (760,280))
        screen.blit(statsTxtSurf,statsTxtRect)
        screen.blit(incrementOrderSurf,incrementOrderRect)
        drawStatsText(screen,selectedSprite,font)
        #Show basic toggle key controls
        screen.blit(toggleLabelsSurf,toggleLabelsRect)
        screen.blit(toggleElectronsSurf,toggleElectronsRect)
        screen.blit(toggleControlsSurf,toggleControlsRect)
        #Draw/blit labels if toggled
        if labelsOn == True:
            screen.blit(statsLabelSurf1,statsLabelRect1)
            screen.blit(statsLabelSurf2,statsLabelRect2)
            screen.blit(boxLabelSurf1,boxLabelRect1)
            screen.blit(boxLabelSurf2,boxLabelRect2)
            screen.blit(graphLabelSurf1,graphLabelRect1)
            screen.blit(graphLabelSurf2,graphLabelRect2)
            screen.blit(gboxLabelSurf1,gboxLabelRect1)
            screen.blit(gboxLabelSurf2,gboxLabelRect2)
            screen.blit(resetLabelSurf1,resetLabelRect1)
            screen.blit(resetLabelSurf2,resetLabelRect2)
            screen.blit(incLabelSurf1,incLabelRect1)
            screen.blit(incLabelSurf2,incLabelRect2)
        #Draw/blit controls if toggled
        if controlsOn == True:
            pygame.draw.rect(screen,'#999999',(750,0,1200,1200))
            pygame.draw.rect(screen,'#000000',(750,0,1200,700),width=3)
            pygame.draw.line(screen,'#000000',(750,40),(1200,40),3)
            screen.blit(controlsSurf,controlsRect)
            screen.blit(upControlSurf,upControlRect)
            screen.blit(downControlSurf,downControlRect)
            screen.blit(stepControlSurf,stepControlRect)
            screen.blit(cControlSurf,cControlRect)
            screen.blit(undoControlSurf,undoControlRect)
            screen.blit(redoControlSurf,redoControlRect)
            screen.blit(lClickControlSurf,lClickControlRect)
            screen.blit(rClickControlSurf,rClickControlRect)
            screen.blit(sControlSurf,sControlRect)
            screen.blit(escControlSurf,escControlRect)
            screen.blit(delControlSurf,delControlRect)
        #Draw graph box
        pygame.draw.line(screen,'#000000',(751,300),(751,600),width=3)
        graphTitleSurf = font.render('Graph',True,'#222222')
        graphTitleRect = graphTitleSurf.get_rect(center = (875,320))
        #If controls not toggled, draw unit graph
        if controlsOn == False:
            pygame.draw.line(screen,'#000000',(785,345),(785,470),width=2)
            pygame.draw.line(screen,'#000000',(785,470),(963,470),width=2)
            #If unit graph is selected, show units and values
            if len(unitGraphGroup) > 0:
                ugraph = unitGraphGroup[0]
                unit1 = ugraph.axies['unit1'][0]
                symbol1 = ugraph.axies['unit1'][1]
                unit2 = ugraph.axies['unit2'][0]
                symbol2 = ugraph.axies['unit2'][1]
                ytitleSurf = font.render(f'{unit1}',True,'#222222')
                ytitleRect = ytitleSurf.get_rect(midright = (780,355))
                yunitSurf = font.render(f'/{symbol1}',True,'#222222')
                yunitRect = yunitSurf.get_rect(midright = (783,375))
                xtitleSurf = font.render(f'{unit2}',True,'#222222')
                xunitSurf = font.render(f'/{symbol2}',True,'#222222')
                xunitRect = xunitSurf.get_rect(midright = (963,485))
                if unit2 == 'LI':
                    xtitleRect = xtitleSurf.get_rect(midright = (920,485))
                elif unit2 == 'T':
                    xtitleRect = xtitleSurf.get_rect(midright = (933,485))
                else:
                    xtitleRect = xtitleSurf.get_rect(midright = (938,485))
                graphTitleSurf = font.render(f'Graph: {unit1} against {unit2}',True,'#222222')
                graphTitleRect = graphTitleSurf.get_rect(center = (874,320))
                #Show selected sprite name under graph
                if selectedSprite:
                    showText = ''
                    if selectedSprite.name == 'junc':
                        showText = 'Junction'
                    elif selectedSprite.name == 'ldr':
                        showText = 'LDR'
                    elif selectedSprite.name == 'cell':
                        showText = 'Cell/Power Source'
                    else:
                        showText = selectedSprite.name.title()
                    graphComponentSurf = font.render(f'({showText})',True,'#222222')
                    graphComponentRect = graphComponentSurf.get_rect(center = (874,520))
                    screen.blit(graphComponentSurf,graphComponentRect)
                screen.blit(graphTitleSurf,graphTitleRect)
                screen.blit(ytitleSurf,ytitleRect)
                screen.blit(yunitSurf,yunitRect)
                screen.blit(xtitleSurf,xtitleRect)
                screen.blit(xunitSurf,xunitRect)
            else:
                screen.blit(graphTitleSurf,graphTitleRect)
            ##If a graph and component is selected, plot lines
            if selectedSprite != None and len(unitGraphGroup) > 0:
                unitGraph = unitGraphGroup[0]
                if unitGraph.unit2 == 'LI':
                    if selectedSprite.name == 'ldr':
                        #Draw r-li relationship
                        unitGraph.plotTempLi(screen)
                    else:
                        #Draw n/a
                        unitGraph.plotNA(screen,font)
                elif unitGraph.unit2 == 'T':
                    if selectedSprite.name == 'thermistor':
                        #Draw r-t relationship
                        unitGraph.plotTempLi(screen)
                    else:
                        #Draw n/a
                        unitGraph.plotNA(screen,font)
                elif unitGraph.unit2 == 'V':
                    if selectedSprite.name == 'diode':
                        #Draw i-v relationship (diode) 
                        unitGraph.plotDiodeV(screen)
                    elif selectedSprite.name == 'lamp' or selectedSprite.name == 'thermistor':
                        #Draw i-v relationship (lamp/thermistor)
                        unitGraph.plotLampThermV(screen)
                    elif selectedSprite.name == 'resistor' or selectedSprite.name == 'ldr':
                        #Draw linear line relationship (resistor/ldr)
                        unitGraph.plotLinear(screen)
                    else:
                        #Draw n/a
                        unitGraph.plotNA(screen,font)
        #If circuit is complete and vectors haven't been made, create vectors and electrons
        if circuitGraph.circuitValid == True:
            if circuitGraph.vectorsMade == False:
                circuitGraph.makeVectors()
        #Get the nearest point as [nearestComponent, nearestConnector (L/R for dragging, and T/B for voltmeter), distanceFromMouse]
        nearestPoint = findNearestConnector(wireOriginSprite)
        #Iterate through sprite group and blit sprites
        for sprite in allSprites:
            #Show any components on the screen
            if sprite in componentSpriteGroup:
                #If mouse hovering on/off component change image to hover/non-hover
                if sprite.rect.collidepoint(pygame.mouse.get_pos()):
                    sprite.hover('Hov')
                else:
                    sprite.hover('')
                #If circuit is valid, set connected components to be active
                if circuitGraph.circuitValid == True:
                    for component in componentSpriteGroup:
                        if sprite.ID in circuitGraph.graph:
                            numberOfConnections = 0
                            for key in sprite.connected:
                                if sprite.connected[key] != None:
                                    numberOfConnections += 1
                            if numberOfConnections == 2:
                                sprite.active = True
                            else:
                                sprite.active = False
                #Show component and update its stored side positions
                screen.blit(sprite.surf,sprite.rect)
                sprite.update()
            else:
                #Show proxCircle at left/right connector if nearest point is found
                if sprite.name == 'proxCircle' and pickup == False and circuitGraph.isCyclic() == False:
                    if nearestPoint[0].name != 'voltmeter':
                        if nearestPoint[0].name == 'junc':
                            #Set smaller image for proxCircle if nearest component is a junction
                            proxCircle.surf = pygame.image.load('graphics/proxCircleSmall.png')
                        else:
                            #Reset to normal image for proxCircle when nearest component is not a junction
                            proxCircle.surf = pygame.image.load('graphics/proxCircle.png')
                        sprite.showClosest(nearestPoint,wireOriginSprite)
                        if nearestPoint[1] != 'top' and nearestPoint[1] != 'bottom':
                            screen.blit(sprite.surf,sprite.rect)
                ##Show wires
                elif sprite.name == 'wire':
                    ##If wire being dragged, set the end to the current mouse position to follow it
                    if makingWire == True and sprite == newWire:
                        sprite.updateEnd(nearestPoint,makingWire,wireOriginSprite,wireOriginConnector)
                        pygame.draw.aaline(screen,sprite.color,sprite.ends[0],sprite.ends[1],5)
                    else:
                        #If not dragging wire, delete it if not connected
                        if sprite.placed == False:
                            if sprite.sprites[0]:
                                if sprite.sprites[0].name != 'voltmeter':
                                    allSprites.remove(sprite)
                                    IDSprites.remove(sprite)
                        #If wire connected, draw it
                        else:
                            sprite.update()
                            pygame.draw.aaline(screen,sprite.color,sprite.ends[0],sprite.ends[1],2)
        ##If circuit is valid, show electrons and update their positions
        if circuitGraph.circuitValid == True:
            for electron in electronSprites:
                if circuitGraph.vectorsMade == True:
                    ex = electron.currentPos[0]
                    ey = electron.currentPos[1]
                    vects = circuitGraph.vectorsCycle
                    emfSign = circuitGraph.emfSign
                    currentMult = circuitGraph.currentMultiplier
                    #Add to electron x position by moveBy vector x value
                    #Emf sign sets the direction (pos/neg/0), currentMultiplier sets the number of times to add "moveBy" for speed
                    ex = ex + currentMult*(emfSign*(vects[electron.vectorIndex][3].moveBy[0]))
                    if vects[electron.vectorIndex][0] == 'vector':
                        #Add to electron y position by moveBy vector y value
                        ey = ey + currentMult*(emfSign*(vects[electron.vectorIndex][3].moveBy[1]))
                    ##If electron has reached the end of its current vector, increment the current vectorIndex to follow the next one
                    if emfSign == 1:
                        if vects[electron.vectorIndex][3].pos2[0] - vects[electron.vectorIndex][3].pos1[0] > 0:
                            if electron.currentPos[0] >= vects[electron.vectorIndex][3].pos2[0]:
                                ex = vects[electron.vectorIndex][3].pos2[0]
                                ey = vects[electron.vectorIndex][3].pos2[1]
                                electron.vectorIndex += 1
                        else:
                            if electron.currentPos[0] <= vects[electron.vectorIndex][3].pos2[0]:
                                ex = vects[electron.vectorIndex][3].pos2[0]
                                ey = vects[electron.vectorIndex][3].pos2[1]
                                electron.vectorIndex += 1
                    elif emfSign == -1:
                        if vects[electron.vectorIndex][3].pos2[0] - vects[electron.vectorIndex][3].pos1[0] > 0:
                            if electron.currentPos[0] <= vects[electron.vectorIndex][3].pos1[0]:
                                ex = vects[electron.vectorIndex][3].pos1[0]
                                ey = vects[electron.vectorIndex][3].pos1[1]
                                electron.vectorIndex -= 1
                        else:
                            if electron.currentPos[0] >= vects[electron.vectorIndex][3].pos1[0]:
                                ex = vects[electron.vectorIndex][3].pos1[0]
                                ey = vects[electron.vectorIndex][3].pos1[1]
                                electron.vectorIndex -= 1
                    if electron.vectorIndex >= len(vects):
                        electron.vectorIndex = 0
                    if electron.vectorIndex < 0:
                        electron.vectorIndex = len(vects)-1
                    #Update new electron position and rectangle
                    electron.currentPos = (ex,ey)
                    electron.rect = electron.surf.get_rect(center = electron.currentPos)
                #Show electron if toggled to show
                if electron.shown == True:
                    screen.blit(electron.surf,electron.rect)
        #If 's' has been pressed in the last 400 event loops
        if screenshotTaken == True and screenshotIteration <= 400:
            #If 's' has been pressed in the current event loop, take screenshot
            if saveScreenshot == True:
                saveScreenshot = False
                pygame.image.save(screen, f'screenshots/screenshot{screenshotNumber}.png')
                with open('screenshots/screenshotData.txt', 'w') as file:
                    screenshotNumber += 1
                    file.write(str(screenshotNumber))
            #Show screenshot message to notify to user
            pygame.draw.rect(screen,'#999999',[200,200,400,100])
            pygame.draw.rect(screen,'#ff4444',[200,200,400,100],width=3)
            ssTakenSurf = fontHuge.render('Screenshot Taken',True,'#3333ee')
            ssTakenRect = ssTakenSurf.get_rect(midleft = (220,235))
            ssSavedSurf = font.render('Saved to screenshots folder',True,'#3333ee')
            ssSavedRect = ssSavedSurf.get_rect(center = (400,270))
            screen.blit(ssTakenSurf,ssTakenRect)
            screen.blit(ssSavedSurf,ssSavedRect)
            screenshotIteration += 1
        else:
            screenshotIteration = 0
            screenshotTaken = False
        
        #Update display and clock
        pygame.display.update()
        clock.tick(300)

#####Threading
#Create pygame and tkinter threads
pygameThread = threading.Thread(target=pygameRun)
tkBoxThread = threading.Thread(target=tkBoxRun)
#Start pygame and tkinter threads
pygameThread.start()
tkBoxThread.start()
