#include <libssh/libssh.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

#define MAX_COMMANDS 100  // Máximo de comandos a almacenar
#define MAX_LENGTH 256    // Tamaño máximo de cada línea

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

// Funcion para ingresar contraseña como interactive keyboard
int authenticate_kbdint(ssh_session session, const char *password) {
    int rc = ssh_userauth_kbdint(session, NULL, NULL);
    while (rc == SSH_AUTH_INFO) {
        int nprompts = ssh_userauth_kbdint_getnprompts(session);
        for (int i = 0; i < nprompts; i++) {
            const char *prompt = ssh_userauth_kbdint_getprompt(session, i, NULL);
            //printf("Prompt: %s\n", prompt);  // Muestra el prompt (puede ser "Password:")
            
            ssh_userauth_kbdint_setanswer(session, i, password);
        }
        rc = ssh_userauth_kbdint(session, NULL, NULL);  // Volver a intentar
    }
    
    return rc;
}

// Leer un archivo .txt para obtener el array de comandos a ejecutar
const char **leer_comandos(const char *filename, int *num_comandos) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Error al abrir el archivo");
        return NULL;
    }

    // Reservar memoria para la lista de comandos
    const char **command_list = malloc(MAX_COMMANDS * sizeof(char *));
    if (!command_list) {
        perror("Error al asignar memoria");
        fclose(file);
        return NULL;
    }

    char buffer[MAX_LENGTH];
    *num_comandos = 0;

    while (fgets(buffer, sizeof(buffer), file) && *num_comandos < MAX_COMMANDS - 1) {
        buffer[strcspn(buffer, "\n")] = 0;  // Eliminar el salto de línea

        // Reservar memoria para cada comando
        command_list[*num_comandos] = strdup(buffer);
        if (!command_list[*num_comandos]) {
            perror("Error al asignar memoria para un comando");
            break;
        }

        (*num_comandos)++;
    }
    fclose(file);

    // Agregar NULL al final de la lista
    command_list[*num_comandos] = NULL;

    return command_list;
}


// Funcion para liberar memoria de un array de strings
void liberar_comandos(const char **command_list, int num_comandos) {
    for (int i = 0; i < num_comandos; i++) {
        free((void *)command_list[i]);
    }
    free(command_list);
}


// FUNCION PRINCIPAL
int main(int argc, char *argv[]) {
    // Verificar que se hayan proporcionado los parámetros necesarios
    if (argc != 4) {
        fprintf(stderr, "Uso: %s <ip> <user> <pass> <timeout>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    // Obtener los parámetros de la línea de comandos
    char *ip_target     = argv[1];          // IP del servidor
    char *username      = argv[2];          // Nombre de usuario
    char *password      = argv[3];          // Contraseña
    //int timeout         = atoi(argv[4]);    // Timeout para inicio de sesion ssh
    const int timeout   = 6;
    
    // Lista de comandos a ejecutar
    int qty_comandos;
    const char **command_ssh_list = leer_comandos("ssh_commands.txt", &qty_comandos);
    if (!command_ssh_list) {
        return 1;
    }

    // Crear una nueva sesión SSH
    ssh_session my_ssh_session;
    int rc;
    int port = 22;
    int verbosity = SSH_LOG_PROTOCOL;
    
    my_ssh_session = ssh_new();
    if (my_ssh_session == NULL){
        exit(-1);
    }
 
    ssh_options_set(my_ssh_session, SSH_OPTIONS_HOST, ip_target);
    ssh_options_set(my_ssh_session, SSH_OPTIONS_USER, username); 
    //ssh_options_set(my_ssh_session, SSH_OPTIONS_LOG_VERBOSITY, &verbosity);
    ssh_options_set(my_ssh_session, SSH_OPTIONS_PORT, &port);
    ssh_options_set(my_ssh_session, SSH_OPTIONS_TIMEOUT, &timeout);

    // Connect to server
    rc = ssh_connect(my_ssh_session);
    if (rc != SSH_OK)
    {
      fprintf(stderr, "Error server: %s\n", ssh_get_error(my_ssh_session));
      ssh_free(my_ssh_session);
      exit(-1);
    }

    // Authenticate stage
    rc = ssh_userauth_password(my_ssh_session, NULL, password);    
    if (rc == SSH_AUTH_DENIED) {
        //printf("Password authentication failed, trying keyboard-interactive...\n");
        rc = authenticate_kbdint(my_ssh_session, password);
    }

    if (rc == SSH_AUTH_SUCCESS) {
        //printf("Authentication successful!\n");
    } else {
        fprintf(stderr, "Error auth: %s\n", ssh_get_error(my_ssh_session));
        ssh_disconnect(my_ssh_session);
        ssh_free(my_ssh_session);
        exit(-1);
    }

    // - - - - - - - - - - - UNA VEZ REALIZADA LA CONEXION, PROCEDEMOS A REALIZAR LAS CONSULTAS POR TERMINAL REMOTO - - - - - - - - //
    // Array para almacenar comandos y respuestas
    ComandoRespuesta resultados[10];  // Ajusta el tamaño según sea necesario
    int num_comandos = 0;

    const int timeout_commands = 2;  // Timeout en segundos
    ssh_options_set(my_ssh_session, SSH_OPTIONS_TIMEOUT, &timeout_commands);
    // Recorrer la lista de comandos y ejecutarlos uno por uno
    for (int i = 0; command_ssh_list[i] != NULL; i++) {
        // Almacenar el comando
        //         Buffer donde para el comando  - comando terminal   -        tamaño del buffer a almacenar
        strncpy(resultados[num_comandos].comando, command_ssh_list[i], sizeof(resultados[num_comandos].comando) - 1);
        resultados[num_comandos].comando[sizeof(resultados[num_comandos].comando) - 1] = '\0';  // Asegurar terminación nula

        // Mostrar el comando
        printf("•%s\n", resultados[num_comandos].comando);

        // Crear un canal para ejecutar el comando
        ssh_channel channel = ssh_channel_new(my_ssh_session);
        if (channel == NULL) {
            fprintf(stderr, "Error: No se pudo crear el canal.\n");
            continue;  // Continuar con el siguiente comando
        }

        rc = ssh_channel_open_session(channel);
        if (rc != SSH_OK) {
            fprintf(stderr, "Error: No se pudo abrir el canal: %s\n", ssh_get_error(my_ssh_session));
            ssh_channel_free(channel);
            continue;  // Continuar con el siguiente comando
        }

        rc = ssh_channel_request_exec(channel, command_ssh_list[i]);
        if (rc != SSH_OK) {
            fprintf(stderr, "Error: Comando inválido: %s\n", ssh_get_error(my_ssh_session));
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
        printf("%s\n", resultados[num_comandos].respuesta);

        num_comandos++;  // Incrementar el contador de comandos
    }

    liberar_comandos(command_ssh_list, qty_comandos);

    // Desconectar y liberar la sesión SSH
    ssh_disconnect(my_ssh_session);
    ssh_free(my_ssh_session);

    return EXIT_SUCCESS;
}
