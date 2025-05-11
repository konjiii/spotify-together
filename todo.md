- features:

- development:
    when not valid login during playlist playing etc: make it sothat the error is handeled and the playlist continues, and that after logingin nothing else needs to be done

    say_to_party: say which party

    closing the app: finish all loops
- bugs:
    Unclosed client session
    client_session: <aiohttp.client.ClientSession object at 0x000001493D514440>
    Unclosed connector
    connections: ['deque([(<aiohttp.client_proto.ResponseHandler object at 0x000001493D4DA9F0>, 824052.9830089)])']
    connector: <aiohttp.connector.TCPConnector object at 0x000001493D514590>