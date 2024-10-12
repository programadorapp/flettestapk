import flet as ft
import requests
import os
import threading  # Para multithreading
class FileUploader(ft.UserControl):  # Herdando de UserControl
    def __init__(self, page, buttont):
        super().__init__()
        self.page = page
        self.buttont = buttont
        self.selected_files = ft.Text()
        self.file_paths = []
        self.pick_files_dialog = ft.FilePicker(on_result=self.pick_files_result)

        # Adiciona o FilePicker à sobreposição da página
        self.page.overlay.append(self.pick_files_dialog)
        self.page.update()  # Atualiza a página após adicionar o FilePicker

        # Cria o botão para selecionar arquivos
        self.buttont.on_click = lambda _: self.pick_files_dialog.pick_files(allow_multiple=True)

        # Adiciona o botão e o texto à interface do usuário
        self.controls.append(ft.Row([self.buttont, self.selected_files]))
    def pick_files_result(self, e: ft.FilePickerResultEvent):
        # Atualiza os caminhos dos arquivos selecionados
        self.selected_files.value = (
            ", ".join(map(lambda f: f.path, e.files)) if e.files else "Cancelled!"
        )
        self.selected_files.update()

    def get_file_paths(self):
        return self.selected_files.value # Retorna os caminhos dos arquivos selecionados

    def build(self):  # Método necessário para UserControl
        return ft.Row([self.buttont, self.selected_files])
class FirebaseClient:
    def __init__(self, api_key, db_url, storage_url):
        self.api_key = api_key
        self.db_url = db_url
        self.storage_url = storage_url
        self.token = None
        self.refresh_token = None

    def get_data(self, path):
        url = f"{self.db_url}/{path}.json?auth={self.token}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json().get('error', {}).get('message', 'Unknown error'))

    def login(self, email, password):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        data = response.json()
        if response.status_code == 200:
            self.token = data['idToken']
            self.refresh_token = data['refreshToken']
            return data
        else:
            raise Exception(data.get('error', {}).get('message', 'Unknown error'))

    def upload_file(self, file_path, destination_path):
        url = f"{self.storage_url}/o?name={destination_path}&uploadType=media"
        headers = {"Authorization": f"Bearer {self.token}"}
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, headers=headers, files=files)
        return response.json()

    def gs_to_https(self, gs_url):
        """
        Converte uma URL gs:// do Firebase Storage para o formato https://
        """
        if not gs_url.startswith("gs://"):
            raise ValueError("A URL deve começar com 'gs://'")
        
        gs_url = gs_url[5:]  # Remover o prefixo gs://
        bucket_name, file_path = gs_url.split("/", 1)
        file_path_encoded = file_path.replace("/", "%2F")
        https_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/{file_path_encoded}?alt=media"
        return https_url 

    def download_image(self, image_url, save_path):
        # Converte a URL gs:// para https://
        http_url = self.gs_to_https(image_url)
        print(f"Baixando imagem de: {http_url}")
        
        # Faz a requisição GET para obter a imagem
        response = requests.get(http_url)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Cria o diretório, se necessário, e salva a imagem
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print("Imagem baixada com sucesso!")
        else:
            print(f"Erro ao baixar a imagem: {response.status_code} - {response.reason}")

    def download_image_async(self, image_url, save_path):
        # Método para baixar imagens em paralelo
        if not os.path.exists(save_path):  # Só faz o download se a imagem não existir
            thread = threading.Thread(target=self.download_image, args=(image_url, save_path))
            thread.start()

# Configurações Firebase
firebase_config = {
    "api_key": "AIzaSyAwLKUA6lUqibNu8uESWogQ7DRRonhtFhg",
    "db_url": "https://cmcbescola-default-rtdb.firebaseio.com",
    "storage_url": "https://firebasestorage.googleapis.com/v0/b/cmcbescola.appspot.com"
}

# Inicializa cliente Firebase
firebase_client = FirebaseClient(
    api_key=firebase_config["api_key"],
    db_url=firebase_config["db_url"],
    storage_url=firebase_config["storage_url"]
)

# Função principal do app Flet
def main(page: ft.Page):
    def tela_login():
        def login(e):
            email_value = email.value
            senha_value = senha.value
            try:
                # Login usando FirebaseClient
                user = firebase_client.login(email_value, senha_value)
                page.add(ft.Text(value="Login sucedido!", bgcolor="green"))
                tela_inicial1(page)  # Chama a tela inicial após o login
            except Exception as ex:
                error_message = f"Erro de login: {ex}"
                page.add(ft.Text(value=error_message, bgcolor="red"))

        app_bar = ft.AppBar(
            title=ft.Text("Estaler"),
            center_title=True,
            bgcolor=ft.colors.WHITE,
        )
        page.appbar = app_bar
        page.bgcolor = ft.colors.BLUE_400

        tela = ft.Text(value="Crie sua senha", bgcolor=ft.colors.PRIMARY, color=ft.colors.BLACK)
        nome = ft.TextField(label="Nome", keyboard_type=ft.KeyboardType.TEXT)
        senha = ft.TextField(label="Senha", keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD)
        email = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL)
        button = ft.CupertinoFilledButton(
            content=ft.Text("Confirmar"),
            opacity_on_click=0.3,
            on_click=login
        )

        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.add(
            ft.Container(
                alignment=ft.alignment.center,
                bgcolor=ft.colors.WHITE,
                content=ft.Column([tela, nome, senha, email, button])
            )
        )
    def confirma(e,urlpedido):
        page.clean()
        page.add(ft.Column([ft.Text(value="enviando..."),ft.ProgressRing()]))
    def pedido(e, chave,valor,nome,dc):
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START
        produtoname = ft.Text(value=str(nome))
        informaçao = ft.Text(value=str(dc))
        preço = ft.Text(value=f"Preço:{valor}")
        imagem = ft.Image(src=f"assets/{chave}.png",width=100,height=200)
        button = ft.ElevatedButton(text="Confirmar Pedido",on_click=lambda e, chave=chave:pedido(e,chave))

        page.clean()
        page.bgcolor = ft.colors.GREEN_900
        app_bar = ft.AppBar(
            title=ft.Text(f"Pedidos de {nome}"),
            leading=ft.IconButton(ft.icons.ARROW_BACK,on_click=lambda _: tela_inicial1(page)),
            center_title=True,
            bgcolor=ft.colors.WHITE,
        )
        page.appbar = app_bar
        page.add(ft.Container(content=ft.ResponsiveRow([produtoname,informaçao,imagem, preço, button]), bgcolor=ft.colors.WHITE,alignment=ft.alignment.center))
    def on_navigation_change(e):
            if e.control.selected_index == 0:
                page.controls.clear()
                tela_inicial1(page)
            elif e.control.selected_index == 1:
                tela_inicial2(page)
            page.update()
    def criar_vendas(e):
        lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        def add_venda(e):
            buttont = ft.ElevatedButton(text="carregar")
            uploader = FileUploader(page,buttont=buttont)
            nome_do_produto = ft.TextField(label="Nome do produto", border=ft.InputBorder.UNDERLINE, color="blue")
            # Obter os caminhos dos arquivos selecionados
            file_paths = uploader.get_file_paths()
            file_paths_text = ft.Text(f"Caminhos dos arquivos: {', '.join(file_paths)}" if file_paths else "Nenhum arquivo selecionado")
            novo_produto = ft.Container(content=ft.Column([nome_do_produto, file_paths_text, uploader]))
            lv.controls.append(novo_produto)  
            lv.update()  # Atualiza a lista de vendas
            page.update()
        page.controls.clear()
        page.bgcolor = ft.colors.CYAN_800
        nome_davenda = ft.TextField(label="Nome da venda", border=ft.InputBorder.UNDERLINE)
        nome_dasenha = ft.TextField(label="Senha", border=ft.InputBorder.UNDERLINE)
        nome_doemail = ft.TextField(label="Email", border=ft.InputBorder.UNDERLINE)

        botton = ft.CupertinoFilledButton(
            content=ft.Text("NOVO PRODUTO"),
            opacity_on_click=0.3,
            on_click=add_venda,
        )

        page.add(ft.Container(content=ft.Column([nome_davenda, nome_dasenha, nome_doemail]), bgcolor=ft.colors.WHITE), lv, botton)
    def tela_inicial2(page: ft.Page):
        page.controls.clear()
        texto = ft.Text(
        value="crie uma nova ",  # Texto padrão
        size=30,
        color="black",
        font_family="Arial",
        )
        page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ADD, on_click=criar_vendas, bgcolor=ft.colors.LIME_300)
        # Adiciona o texto ao layout da página
        page.add(texto)
    def tela_inicial1(page: ft.Page):
        page.clean()
        page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.FOOD_BANK, label="vendas"),
            ft.NavigationBarDestination(icon=ft.icons.HOUSE, label="criar"),
         ],
         on_change=on_navigation_change
        )
        app_bar = ft.AppBar(
            title=ft.Text("Estaler"),
            leading=ft.IconButton(ft.icons.UPDATE,on_click=lambda _: tela_inicial1(page)),
            center_title=True,
            bgcolor=ft.colors.WHITE,
            actions=[
                ft.IconButton(ft.icons.NOTIFICATIONS_ACTIVE_OUTLINED, on_click=lambda e: print("Notificações")),
                ft.IconButton(ft.icons.SETTINGS, on_click=lambda e: print("Configurações"))
            ]
        )
        page.appbar = app_bar
        page.bgcolor = ft.colors.BLUE_400
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        coluner = ft.ResponsiveRow()
        
        informe = firebase_client.get_data("vendas")
        
        coluner = ft.ResponsiveRow()

        # Iterar sobre os dados retornados
        for item_key, item_value in informe.items():
            nome = item_value.get('nome', item_key)
            valor = item_value.get('valor', '0,00')
            descris = item_value.get('dscc', 'sem informações')

            if 'imagem' in item_value:
                image_url = item_value['imagem']
                save_path = f"assets/{item_key}.png"
                firebase_client.download_image_async(image_url, save_path)  # Faz download em thread
            
            # Criar o Container
            item_container = ft.Container(
                content=ft.Column([
                    ft.Text(value=f"Nome: {nome}", size=16),
                    ft.Image(src=f"assets/{item_key}.png", width=100, height=100),
                    ft.Text(value=f"Preço: {valor}", size=14, bgcolor="black"),
                ]),
                alignment=ft.alignment.center,
                bgcolor=ft.colors.WHITE,
                col={"sm": 6, "md": 3, "xl": 4},
                border_radius=10,
                width=100,
                height=200,
                padding=10,
                on_click=lambda e, chave=item_key, val=valor, nm=nome, desc=descris: pedido(e, chave, val, nm, desc),
                margin=10
            )

            coluner.controls.append(item_container)

        lv.controls.append(coluner)
        page.add(lv)

    tela_inicial1(page)

ft.app(target=main)
