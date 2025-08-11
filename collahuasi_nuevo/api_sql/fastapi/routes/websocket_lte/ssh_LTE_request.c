#include <libssh/libssh.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h> 

// Estructura para almacenar un comando y su respuesta
typedef struct {
    char comando[256];
    char respuesta[1024];
} ComandoRespuesta;

// Función para eliminar saltos de línea y retornos de carro
void eliminar_saltos_de_linea(char *str) {
    char *src = str, *dst = str;
    while (*src) {
        if (*src != '\n' && *src != '\r') {
            *dst++ = *src;
        }
        src++;
    }
    *dst = '\0';
}

int main(int argc, char *argv[]) {
    // Verificar que se hayan proporcionado los parámetros necesarios
    if (argc != 4) {
        fprintf(stderr, "Uso: %s <ip> <user> <pass>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    // Obtener los parámetros de la línea de comandos
    char *hostname = argv[1];  // IP del servidor
    char *username = argv[2];  // Nombre de usuario
    char *password = argv[3];  // Contraseña
    //int time_delay = atoi(argv[4]); // Tiempo falso de delay


    // Verificar que el tiempo es positivo
    /*
    if (time_delay <= 0) {
        fprintf(stderr, "El tiempo debe ser un valor mayor que 0.\n");
        return 1;
    }
    */

    ssh_session my_ssh_session;
    int rc;

    // Lista de comandos a ejecutar
    const char *command_ssh_list[] = {
        "/interface/lte/monitor lte1 once",
        "/interface print detail",
        "/interface/lte/print detail",
        "/interface/lte/at-chat [find] input=\"AT\\$GPSACP\"",
        NULL  // Marca el final de la lista
    };

    // Crear una nueva sesión SSH
    my_ssh_session = ssh_new();
    if (my_ssh_session == NULL) {
        fprintf(stderr, "Error al crear la sesión SSH.\n");
        exit(EXIT_FAILURE);
    }

    // Configurar opciones de la sesión
    ssh_options_set(my_ssh_session, SSH_OPTIONS_HOST, hostname);
    ssh_options_set(my_ssh_session, SSH_OPTIONS_USER, username);

    // Ignorar la verificación del host (known_hosts)
    ssh_options_set(my_ssh_session, SSH_OPTIONS_STRICTHOSTKEYCHECK, "no");

    // Conectar al servidor
    rc = ssh_connect(my_ssh_session);
    if (rc != SSH_OK) {
        fprintf(stderr, "Error al conectar: %s\n", ssh_get_error(my_ssh_session));
        ssh_free(my_ssh_session);
        exit(EXIT_FAILURE);
    }

    // Autenticación con contraseña
    rc = ssh_userauth_password(my_ssh_session, NULL, password);
    if (rc != SSH_AUTH_SUCCESS) {
        fprintf(stderr, "Error en la autenticación: %s\n", ssh_get_error(my_ssh_session));
        ssh_disconnect(my_ssh_session);
        ssh_free(my_ssh_session);
        exit(EXIT_FAILURE);
    }

    // Array para almacenar comandos y respuestas
    ComandoRespuesta resultados[10];  // Ajusta el tamaño según sea necesario
    int num_comandos = 0;

    // Recorrer la lista de comandos y ejecutarlos uno por uno
    for (int i = 0; command_ssh_list[i] != NULL; i++) {
        // Almacenar el comando
        strncpy(resultados[num_comandos].comando, command_ssh_list[i], sizeof(resultados[num_comandos].comando) - 1);
        resultados[num_comandos].comando[sizeof(resultados[num_comandos].comando) - 1] = '\0';  // Asegurar terminación nula

        // Mostrar el comando
        printf("->%s\n", resultados[num_comandos].comando);

        // Crear un canal para ejecutar el comando
        ssh_channel channel = ssh_channel_new(my_ssh_session);
        if (channel == NULL) {
            fprintf(stderr, "Error al crear el canal.\n");
            continue;  // Continuar con el siguiente comando
        }

        rc = ssh_channel_open_session(channel);
        if (rc != SSH_OK) {
            fprintf(stderr, "Error al abrir el canal: %s\n", ssh_get_error(my_ssh_session));
            ssh_channel_free(channel);
            continue;  // Continuar con el siguiente comando
        }

        rc = ssh_channel_request_exec(channel, command_ssh_list[i]);
        if (rc != SSH_OK) {
            fprintf(stderr, "Error al ejecutar el comando: %s\n", ssh_get_error(my_ssh_session));
            ssh_channel_close(channel);
            ssh_channel_free(channel);
            continue;  // Continuar con el siguiente comando
        }

        // Leer la salida del comando
        char buffer[1024];
        int nbytes;
        resultados[num_comandos].respuesta[0] = '\0';  // Inicializar la respuesta
        while ((nbytes = ssh_channel_read(channel, buffer, sizeof(buffer) - 1, 0)) > 0) {
            buffer[nbytes] = '\0';  // Asegurar terminación nula
            strncat(resultados[num_comandos].respuesta, buffer, sizeof(resultados[num_comandos].respuesta) - 1);
        }
        
        // Eliminar saltos de línea innecesarios
        //eliminar_saltos_de_linea(resultados[num_comandos].respuesta);
        resultados[num_comandos].respuesta[sizeof(resultados[num_comandos].respuesta) - 1] = '\0';  // Asegurar terminación nula

        // Cerrar el canal
        ssh_channel_send_eof(channel);
        ssh_channel_close(channel);
        ssh_channel_free(channel);

        // Mostrar la respuesta
        printf("•%s\n", resultados[num_comandos].respuesta);

        num_comandos++;  // Incrementar el contador de comandos
    }

    // Desconectar y liberar la sesión SSH
    ssh_disconnect(my_ssh_session);
    ssh_free(my_ssh_session);

    return EXIT_SUCCESS;
}
