
const express = require('express');
const respuesta = require('../../red/respuestas');
const controlador = require("./controlador");

const transporter = require("../../mail")

const router = express.Router();

router.post('/sendMail',sendMail );



async function sendMail(req, res, next) {

    let items = req.body.mail;
    let toMail = req.body.toMail;
    let htmlBody = ``;

    let htmlTableTH = `
    <html>
        <head> 
            <style> 
                .tableTimeDown th{
                    padding: 5px 10px;
                }
                .tableTimeDown, .tableTimeDown td {
                    border: 1px solid black;
                    border-collapse: collapse;
                    padding: 5px 10px;
                }
                .tableTimeDown tr:hover {
                    background-color: black;
                    color: white;
                }
            </style>
        </head>
        <body>
            <p> Estimados Sr(es), </p>
            <p> Se adjunta lista de equipos a tomar en cuenta que el sistema SMARTLINK tiene registro que están sin comunicación : </p>
            <table class='tableTimeDown'>
                <tr> 
                    <th> Ip </th>
                    <th> Nombre </th>
                    <th> Tiempo sin comunicacion </th>
                    <th> Hora inicio  </th>
                </tr>
    `

    let htmlTableFooter = 
    `
            </table>
        </body>
    </html>
    `

    items.forEach((item) => {
        // console.log('item.dateDown',item.dateDown, item.dateDown.length)
       htmlBody += `<tr> 
            <td>${item.ip}</td>
            <td>${item.hostname}</td>
            <td>${item.timeDown} min</td>
            <td>${item.dateDown.length == 0 ? '+ 1 día sin conexión' : item.dateDown}</td>
        </tr>` 
    })

    // <td>${item.dateDown === '' ? '+ 1 día sin conexión' : item.dateDown}</td>

    let finalHTML = htmlTableTH + htmlBody + htmlTableFooter


    let email = {
        from: 'mauricioaransan@gmail.com',
        to : toMail,
        subject: 'Equipos sin Conexion',
        text : 'Lista de Equipos sin Conexion',
        html : `${finalHTML}`
    }

    transporter.sendMail(email, (error, info  )=>{
        if(error) {
            console.error('hay un error')
        } else {
            console.log('MAIL enviado con EXITO')
            respuesta.success(req, res, 'ENVIADO', 200);
        }
    })

}

module.exports = router;
