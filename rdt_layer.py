from segment import Segment


# #################################################################################################################### #
# RDTLayer                                                                                                             #
#                                                                                                                      #
# Description:                                                                                                         #
# The reliable data transfer (RDT) layer is used as a communication layer to resolve issues over an unreliable         #
# channel.                                                                                                             #
#                                                                                                                      #
#                                                                                                                      #
# Notes:                                                                                                               #
# This file is meant to be changed.                                                                                    #
#                                                                                                                      #
#                                                                                                                      #
# #################################################################################################################### #


class RDTLayer(object):
    # ################################################################################################################ #
    # Class Scope Variables                                                                                            #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    DATA_LENGTH = 4  # in characters                     # The length of the string data that will be sent per packet...
    FLOW_CONTROL_WIN_SIZE = 15  # in characters          # Receive window size for flow-control
    sendChannel = None
    receiveChannel = None
    dataToSend = ''
    currentIteration = 0                                # Use this for segment 'timeouts'
    # Add items as needed
    recvdData = {}
    recvWindow = [0, 12]
    nextSeqNum = 0
    lastAck = 0
    sendWindowBase = 0
    sendWindowEnd = 12
    countSegmentTimeouts = 0
    timeWaiting = 0
    clientAckLog = []
    serverAckLog = []

    # ################################################################################################################ #
    # __init__()                                                                                                       #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def __init__(self):
        self.sendChannel = None
        self.receiveChannel = None
        self.dataToSend = ''
        self.currentIteration = 0
        # Add items as needed
        self.status = None



    # ################################################################################################################ #
    # setSendChannel()                                                                                                 #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the unreliable sending lower-layer channel                                                 #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setSendChannel(self, channel):
        self.sendChannel = channel

    # ################################################################################################################ #
    # setReceiveChannel()                                                                                              #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the unreliable receiving lower-layer channel                                               #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setReceiveChannel(self, channel):
        self.receiveChannel = channel

    # ################################################################################################################ #
    # setDataToSend()                                                                                                  #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the string data to send                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setDataToSend(self,data):
        self.dataToSend = data

    # ################################################################################################################ #
    # getDataReceived()                                                                                                #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to get the currently received and buffered string data, in order                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def getDataReceived(self):
        # ############################################################################################################ #
        # Identify the data that has been received...
        # ############################################################################################################ #
        dataReceived = ''
        for value in self.recvdData.values():
            dataReceived += value
        return dataReceived

    # ################################################################################################################ #
    # processData()                                                                                                    #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # "timeslice". Called by main once per iteration                                                                   #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processData(self):
        self.currentIteration += 1
        self.processSend()
        self.processReceiveAndSendRespond()

    # ################################################################################################################ #
    # processSend()                                                                                                    #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Manages Segment sending tasks                                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processSend(self):

        # Set the status of the transmission to either Client or Server
        if self.dataToSend:
            self.status = "Client"

            # Separate the data to be sent from the Client into chunks, which are stored in a dictionary object
            chunkSize = self.DATA_LENGTH

            dataDict = {i * chunkSize: self.dataToSend[i * chunkSize:(i + 1) * chunkSize]
                        for i in range((len(self.dataToSend) + chunkSize - 1) // chunkSize)}


        else:
            self.status = "Server"

        # ############################################################################################################ #
        # You should pipeline segments to fit the flow-control window
        # The flow-control window is the constant RDTLayer.FLOW_CONTROL_WIN_SIZE
        # The maximum data that you can send in a segment is RDTLayer.DATA_LENGTH
        # These constants are given in # characters

        # Somewhere in here you will be creating data segments to send.
        # The data is just part of the entire string that you are trying to send.
        # The seqnum is the sequence number for the segment (in character number, not bytes)

        if self.status == "Client":

            # If the Client expects an Ack but does not receive it, it waits 3 iterations, then re-sends segments
            # starting from the last received cumulative Ack (simulated Timeout)
            if not self.receiveChannel.receiveQueue and self.currentIteration > 1:
                if self.timeWaiting == 3:
                    self.nextSeqNum = self.sendWindowBase
                    self.countSegmentTimeouts += 1
                    self.timeWaiting = 0                  # Resets timeout clock
                else:
                    self.timeWaiting += 1
                    return

            # When the Client receives a cumulative Ack, it adjusts its send window accordingly
            elif self.receiveChannel.receiveQueue:
                recvdSeg = self.receiveChannel.receive()
                recvdAck = recvdSeg[-1].acknum

                self.sendWindowBase = recvdAck
                self.sendWindowEnd = self.sendWindowBase + (self.DATA_LENGTH * 3)
                self.nextSeqNum = self.sendWindowBase

            # (Optional) Adds a log entry for ack packets received by the Client from the Server
            # These entries could potentially be used to send ack packets from Client to Server,
            # though it is not implemented to keep iterations down and preserve the Flow Control Window
                self.clientAckLog.append(recvdAck)
                #print(f"Client Ack Log: {self.clientAckLog}")

            # Client prepares up to 3 packets for transmission, beginning with the seq # at the base of its send window
            for i in range(self.sendWindowBase, self.sendWindowEnd, self.DATA_LENGTH):
                if self.nextSeqNum <= len(dataDict) * self.DATA_LENGTH - 1:
                    segmentSend = Segment()
                    seqnum = self.nextSeqNum
                    data = dataDict[seqnum]

        # ############################################################################################################ #
        # Display sending segment
                    segmentSend.setData(seqnum, data)
                    print("Sending segment: ", segmentSend.to_string())
                    self.nextSeqNum += self.DATA_LENGTH

        # Use the unreliable sendChannel to send the segment
                    self.sendChannel.send(segmentSend)

        # Reset the timeout counter to the oldest unacknowledged packet
            self.timeWaiting = 0

    # ################################################################################################################ #
    # processReceive()                                                                                                 #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Manages Segment receive tasks                                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processReceiveAndSendRespond(self):

        # This call returns a list of incoming segments (see Segment class)...
        listIncomingSegments = self.receiveChannel.receive()

        # ############################################################################################################ #
        # What segments have been received?
        # How will you get them back in order?
        # This is where a majority of your logic will be implemented
        if listIncomingSegments:

            # The Server's receive window is 15 characters, meaning only 3 packets of size 4 characters will fit.
            # This operation ensures that only 3 packets from the Server's receive window can be processed
            # per iteration, as there is no buffer. Any additional packets are dropped.
            listIncomingSegments = listIncomingSegments[:3]

            segmentAck = Segment()                  # Segment acknowledging packet(s) received

            # This is the last cumulative Ack sent from the Server, and represents the base of its receive window
            lastAck = self.recvWindow[0]

            # If a packet passes the checksum and has yet to be acknowledged, its data is added to the Server's
            # recvdData object and the cumulative Ack is updated.
            for i in range(len(listIncomingSegments)):
                if (listIncomingSegments[i].checkChecksum()) and listIncomingSegments[i].seqnum == lastAck:
                    index = listIncomingSegments[i].seqnum
                    self.recvdData[index] = listIncomingSegments[i].payload
                    while lastAck in self.recvdData.keys():
                        lastAck += self.DATA_LENGTH

        # ############################################################################################################ #
        # How do you respond to what you have received?
        # How can you tell data segments apart from ack segments?
        # Somewhere in here you will be setting the contents of the ack segments to send.
        # The goal is to employ cumulative ack, just like TCP does...

        # Updates the Server's receive window based on the current cumulative Ack
                ackNum = lastAck
                self.recvWindow[0] = ackNum
                self.recvWindow[1] = ackNum + (self.DATA_LENGTH * 3)


        # ############################################################################################################ #
        # Display response segment
                segmentAck.setAck(ackNum)
                print("Sending ack: ", segmentAck.to_string())

        # Use the unreliable sendChannel to send the ack packet
                self.sendChannel.send(segmentAck)

        # (Optional) Adds a log entry to the Server side of cumulative ack packets sent and/or prints the log
            self.serverAckLog.append(ackNum)
            #print(f"Server Ack Log: {self.serverAckLog}")
