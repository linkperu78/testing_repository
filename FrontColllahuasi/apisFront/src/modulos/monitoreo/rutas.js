const express = require("express");
const zmq = require("zeromq/v5-compat");
const respuesta = require("../../red/respuestas");
// const zmq = require("zeromq/v5-compat");
// const WebSocket = require("ws");
// const wss = new WebSocket.Server({ port: 2385 });

const router = express.Router();

/*************************
 ********* RUTAS *********
 *************************/

///////////////////////
////// Principal //////
///////////////////////
router.get("/getAllDataGestor", getAllDataGestor);

async function getAllDataGestor(req, res, next) {
  try {
    // const subscriber = zmq.socket("sub");
    // subscriber.connect("tcp://localhost:5555");
    // subscriber.subscribe(""); // Suscribirse a todos los mensajes

    // wss.on("connection", (ws) => {
    //   console.log("Cliente conectado");

    //   // Enviar mensajes al cliente cuando lleguen por ZeroMQ
    //   subscriber.on("message", (message) => {
    //     ws.send(message.toString());
    //   });

    //   // Manejar la desconexión del cliente
    //   ws.on("close", () => {
    //     console.log("Cliente desconectado");
    //   });
    // });

    // console.log("Servidor WebSocket escuchando en ws://localhost:2385");

    respuesta.success(req, res, "HECHO", 200);
    // let items = {};
    // const subscriber = zmq.socket("sub");

    // // Conectar el socket al servidor en el puerto 5555
    // subscriber.connect("tcp://localhost:5555");

    // // Suscribirse a todos los mensajes (o a un tema específico)
    // subscriber.subscribe(""); // Para recibir todos los mensajes

    // // console.log("Conectado al servidor en el puerto 5555...");

    // // Escuchar mensajes del servidor
    // subscriber.on("message", (message) => {
    //   const mensaje = JSON.parse(message.toString()); // Convertir el mensaje a JSON
    //   items = mensaje;
    // });
    // // setInterval(() => {
    // // }, 5000);
    // // await controlador.getAllDataGestor(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
