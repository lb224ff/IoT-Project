import * as fs from "node:fs";
import * as http from "node:http";
import * as path from "node:path";
import { StringDecoder } from "node:string_decoder";
import { WebSocketServer } from "ws";

function fromBytes(buffer)
{
  const bytes = new Uint8ClampedArray(buffer);
  const size = bytes.byteLength;
  let x = 0;
  for (let i = 0; i < size; i++)
  {
    const byte = bytes[i];
    x *= 0x100;
    x += byte;
  }
  return x;
}

const PORT = 8000;
const WSPORT = 8080;

const MIME_TYPES = {
  default: "application/octet-stream",
  html: "text/html; charset=UTF-8",
  js: "application/javascript",
  css: "text/css",
  png: "image/png",
  jpg: "image/jpg",
  gif: "image/gif",
  ico: "image/x-icon",
  svg: "image/svg+xml",
};

const STATIC_PATH = path.join(process.cwd(), "./static");

const toBool = [() => true, () => false];

const prepareFile = async (url) => {
  const paths = [STATIC_PATH, url];
  if (url.endsWith("/")) paths.push("index.html");
  const filePath = path.join(...paths);
  const pathTraversal = !filePath.startsWith(STATIC_PATH);
  const exists = await fs.promises.access(filePath).then(...toBool);
  const found = !pathTraversal && exists;
  const streamPath = found ? filePath : STATIC_PATH + "/404.html";
  const ext = path.extname(streamPath).substring(1).toLowerCase();
  const stream = fs.createReadStream(streamPath);
  return { found, ext, stream };
};

let latestSensorData = [0,0,0,0];

const server = http.createServer(async (req, res) => 
{
    let buffer ="";
    let sensorData = [];
    let decoder = new StringDecoder('utf-8');

    req.on('data', function(data)
    {
      console.log('data');
      buffer += decoder.write(data);

      console.log(data.length)

      let sensorPos = 0;
      if(data.length == 8)
      {
        for (let count = 0; count < data.length - 1; count += 2)
        {
          let byteBuffer = [data[count], data[count + 1]];
          let byteNumber = fromBytes(byteBuffer);
          sensorData[sensorPos] = byteNumber;
          sensorPos++; 
        }
        console.log(sensorData);
        latestSensorData = sensorData;
        BroadCastLatestSensorDataToAllClients();
      }
    })
    req.on('end', function()
    {
        console.log('end')
        buffer += decoder.end();
        console.log(buffer);
    })

    const file = await prepareFile(req.url);
    const statusCode = file.found ? 200 : 404;
    const mimeType = MIME_TYPES[file.ext] || MIME_TYPES.default;
    res.writeHead(statusCode, { "Content-Type": mimeType });
    file.stream.pipe(res);
    console.log(`${req.method} ${req.url} ${statusCode}`);
  }
  );
  
  const webSocketServer = new WebSocketServer({port: WSPORT });

  function BroadCastLatestSensorDataToAllClients()
  {
    webSocketServer.clients.forEach(function each(client)
    {
      client.send(JSON.stringify({type: "data", data: latestSensorData}))
    });
  }

  webSocketServer.on('connection', function(webSocket)
  {
    webSocket.on('message', function(data)
    {
      console.log('recieved: %s', data);
      webSocket.send(JSON.stringify({type: "data", data: latestSensorData}));
    });

    webSocket.on('close', function()
    {
      console.log("disconnected client:" + webSocket.url);
    });
  });


  server.listen(PORT, 'Your IP', () =>
  {
    console.log(`Server running at Your IP:${PORT}/`);
  })
