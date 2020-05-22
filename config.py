import player
import client

state_class_map = {
    client.Client: player.CaptainState,
    client.Client: player.FirstMateState,
    client.Client: player.EngineerState,
    client.Client: player.RadioOperatorState,
    }