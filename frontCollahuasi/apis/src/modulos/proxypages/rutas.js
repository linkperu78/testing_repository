const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");
// const { createProxyMiddleware } = require('http-proxy-middleware');
const proxy = require('express-http-proxy');

const router = express.Router();

// const proxyOptions = {
//   target: 'https://jsonplaceholder.typicode.com/users',
//   changeOrigin: true, 
// };



// router.get("/getproxy", proxy);
router.get("/getproxytest", proxy('http://192.168.3.98/', {
  https: true
}));
// router.get("/getproxytest", getTesteoData);
router.get("/getalldata", getAllData);

async function getTesteoData(req, res, next) {
  try {
    
    const proxy = await proxy('http://www.google.com.pe', {
  https: true
});

    await console.log(proxy)
    // const statusCode    = 200;

    // await res.status(statusCode).send({
    //     error:  false,
    //     status: statusCode,
    //     body:   proxy
    // });

    // await console.log(proxy)
    // await controlador.getAllData(res);
  } catch (error) {
    next(error);
  }
}

async function getAllData(req, res, next){
  try {    
    await controlador.getAllData(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;