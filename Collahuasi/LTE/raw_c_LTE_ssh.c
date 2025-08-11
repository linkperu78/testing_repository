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

// Función para verificar el host
int verify_knownhost(ssh_session session)
{
  int state, hlen;
  unsigned char *hash = NULL;
  char *hexa;
  char buf[10];

  state = ssh_is_server_known(session);

  hlen = ssh_get_pubkey_hash(session, &hash);
  if (hlen < 0)
    return -1;

  switch (state)
  {
    case SSH_SERVER_KNOWN_OK:
      break; /* ok */

    case SSH_SERVER_KNOWN_CHANGED:
      fprintf(stderr, "Host key for server changed: it is now:\n");
      ssh_print_hexa("Public key hash", hash, hlen);
      fprintf(stderr, "For security reasons, connection will be stopped\n");
      free(hash);
      return -1;

    case SSH_SERVER_FOUND_OTHER:
      fprintf(stderr, "The host key for this server was not found but another"
        "type of key exists.\n");
      fprintf(stderr, "An attacker might change the default server key to"
        "confuse your client into thinking the key does not exist\n");
      free(hash);
      return -1;

    case SSH_SERVER_FILE_NOT_FOUND:
      fprintf(stderr, "Could not find known host file.\n");
      fprintf(stderr, "If you accept the host key here, the file will be"
       "automatically created.\n");
      /* fallback to SSH_SERVER_NOT_KNOWN behavior */

    case SSH_SERVER_NOT_KNOWN:
      hexa = ssh_get_hexa(hash, hlen);
      fprintf(stderr,"The server is unknown. Do you trust the host key?\n");
      fprintf(stderr, "Public key hash: %s\n", hexa);
      free(hexa);
      if (fgets(buf, sizeof(buf), stdin) == NULL)
      {
        free(hash);
        return -1;
      }
      if (strncasecmp(buf, "yes", 3) != 0)
      {
        free(hash);
        return -1;
      }
      if (ssh_write_knownhost(session) < 0)
      {
        fprintf(stderr, "Error %s\n", strerror(errno));
        free(hash);
        return -1;
      }
      break;

    case SSH_SERVER_ERROR:
      fprintf(stderr, "Error %s", ssh_get_error(session));
      free(hash);
      return -1;
  }

  free(hash);
  return 0;
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
    if (argc != 5) {
        fprintf(stderr, "Uso: %s <ip> <user> <pass>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    // Obtener los parámetros de la línea de comandos
    char *ip_target     = argv[1];          // IP del servidor
    char *username      = argv[2];          // Nombre de usuario
    char *password      = argv[3];          // Contraseña
    int timeout         = atoi(argv[4]);    // Timeout para inicio de sesion ssh

    
    // Lista de comandos a ejecutar
    int num_comandos;
    const char **command_ssh_list = leer_comandos("ssh_commands.txt", &num_comandos);
    if (!command_ssh_list) {
        return 1;
    }

        // Imprimir los comandos leídos
        printf("Comandos leídos:\n");
        for (int i = 0; command_ssh_list[i] != NULL; i++) {
            printf("%d: %s\n", i + 1, command_ssh_list[i]);
        }

        // Liberar memoria
        liberar_comandos(command_ssh_list, num_comandos);
        return 0;

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
      fprintf(stderr, "Error: %s\n", ssh_get_error(my_ssh_session));
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
        fprintf(stderr, "Error: %s\n", ssh_get_error(my_ssh_session));
    }

    // - - - - - - - - - - - UNA VEZ REALIZADA LA CONEXION, PROCEDEMOS A REALIZAR LAS CONSULTAS POR TERMINAL REMOTO - - - - - - - - //
    // Array para almacenar comandos y respuestas
    ComandoRespuesta resultados[10];  // Ajusta el tamaño según sea necesario
    int num_comandos = 0;

    // Recorrer la lista de comandos y ejecutarlos uno por uno
    for (int i = 0; command_ssh_list[i] != NULL; i++) {
        // Almacenar el comando
        //         Buffer donde para el comando  - comando terminal   -        tamaño del buffer a almacenar
        strncpy(resultados[num_comandos].comando, command_ssh_list[i], sizeof(resultados[num_comandos].comando) - 1);
        resultados[num_comandos].comando[sizeof(resultados[num_comandos].comando) - 1] = '\0';  // Asegurar terminación nula

        // Mostrar el comando
        printf("->%s\n", resultados[num_comandos].comando);

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
        printf("•%s\n", resultados[num_comandos].respuesta);

        num_comandos++;  // Incrementar el contador de comandos
    }

    liberar_comandos(command_ssh_list, num_comandos);

    // Desconectar y liberar la sesión SSH
    ssh_disconnect(my_ssh_session);
    ssh_free(my_ssh_session);

    return EXIT_SUCCESS;
}
