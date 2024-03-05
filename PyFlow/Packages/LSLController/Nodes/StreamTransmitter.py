import multiprocessing
import random

from PyFlow.Core import NodeBase
from PyFlow.Core.NodeBase import NodePinsSuggestionsHelper
from PyFlow.Core.Common import *
from pylsl import StreamInlet, resolve_streams, pylsl, StreamInfo, StreamOutlet
from PyFlow.Packages.PyFlowBase.Nodes import FLOW_CONTROL_COLOR

#DemoNode
# LSL_Writer
class StreamTransmitter(NodeBase):
    def __init__(self, name):
        super(StreamTransmitter, self).__init__(name)

        self.beginPin = self.createInputPin("Begin", 'ExecPin', None, self.start)
        self.stopPin = self.createInputPin("Stop", 'ExecPin', None, self.stop)
        self.streamName = self.createInputPin("Name", 'StringPin')
        self.streamType = self.createInputPin("Type", 'StringPin')
        self.streamID = self.createInputPin("ID", 'StringPin')
        self.Data = self.createInputPin('Data', 'AnyPin', structure=StructureType.Multi)
        self.Data.enableOptions(PinOptions.AllowMultipleConnections | PinOptions.AllowAny | PinOptions.DictElementSupported)
        self.Data.disableOptions(PinOptions.SupportsOnlyArrays)

        self.Info_Stream = self.createOutputPin('Info', 'AnyPin', structure=StructureType.Single)
        self.Info_Stream.enableOptions(PinOptions.AllowAny)
        self.Send = self.createOutputPin('DataOut', 'AnyPin', structure=StructureType.Multi)
        self.Send.enableOptions(PinOptions.AllowAny)

        self.bWorking = False
        self.outlet = None
        self.info = None
        self.headerColor = FLOW_CONTROL_COLOR
        self.On = False

        self.DataBase = dict()
        self.channels_dicts=dict()
        self.start = time.time()
        self.counter = 0

        self.q = multiprocessing.Queue()
        self.Prosess = multiprocessing.Process(target=Sender, args=(self.q,))

    def Tick(self, delta):
        super(StreamTransmitter, self).Tick(delta)
        if self.bWorking:

            # Generate a random value
            sample = list(self.Data.getData().values())

            self.addDataToDict(self.streamName.getData(),sample)

            self.Send.setData(self.DataBase)
            # Send the data sample
            #self.outlet.push_sample(sample)
            self.q.put(sample)

    def addDataToDict(self, key, data):
        for i, row in enumerate(self.DataBase[key]):
            self.DataBase[key][row].append(data[i])

    def get_all_keys(self, array_of_dicts):
        keys = dict()
        channels_dicts = dict()
        i = 0
        for key in array_of_dicts.keys():
            keys.update({i: [key, ""]})
            self.channels_dicts[key] = []
            i += 1

        return keys

    def get_all_keys2(self, array_of_dicts,info):
        keys = dict()
        channels_dicts = dict()
        i = 0
        for key in array_of_dicts.keys():
            info.desc().append_child_value("channel", key)
            i += 1

        return info

    @staticmethod
    def keywords():
        return []

    @staticmethod
    def description():
        return "Description in rst format."

    def stop(self, *args, **kwargs):
        self.bWorking = False
        self.On = False

    def start(self, *args, **kwargs):
        data=self.Data.getData()
        if len(self.Data.getData()) >= 1:
            stream_name = self.streamName.getData()
            stream_type = self.streamType.getData()
            channel_count = len(self.Data.getData())
            stream_desc = {
                "Name": stream_name,
                "Type": stream_type,
                "Channels": channel_count,
                "Sampling Rate": 20,
                "Channels Info": self.get_all_keys(data),
            }

        self.DataBase[stream_name] = self.channels_dicts
        #self.outlet = StreamOutlet(info)
        print("Flag1")
        self.Prosess.start()
        self.q.put(stream_desc)
        self.q.put(stream_desc)

        self.bWorking = True
        self.Info_Stream.setData(dict(stream_name=stream_desc))

    @staticmethod
    def category():
        return 'Transmitters'


def Sender(q):
    info_string = q.get()
    info = StreamInfo(
        name=info_string["Name"],
        type=info_string["Type"],
        channel_count=info_string["Channels"],
        nominal_srate=20,
        channel_format='float32',
        source_id="ID1"
    )
    print("hi")
    info_channels = info.desc().append_child("channels")
    for name in Init_Channel_Names(info_string["Channels Info"]):
        info_channels.append_child("channel").append_child_value("label", name)
    print("hi hi")
    outlet = StreamOutlet(info)

    outlet = StreamOutlet(info)
    while True:
        if q.get() is not None:
            samples=q.get()
            outlet.push_sample(samples)

def Init_Channel_Names( dictio):
    dict_keys = []
    for key in dictio:
        dict_keys.append(dictio[key][0])
    return dict_keys