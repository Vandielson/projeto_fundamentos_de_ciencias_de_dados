# 📦 Dashboard de Logística

## 🧠 Descrição do Projeto
Este projeto foi desenvolvido como parte da disciplina **Fundamentos em Ciência de Dados**, ministrada pelo professor **Assuero Fonseca Ximenes**, no período **2025.2**.  

O objetivo é criar um **Dashboard interativo em Python utilizando Streamlit**, que permita aos gestores monitorar e analisar o estoque de produtos de uma empresa de forma dinâmica e intuitiva.

## 🧰 Tecnologias Utilizadas

- **Python 3.12+**
- **Streamlit**
- **Pandas**
- **Matplotlib / Seaborn**

## 🗂️ Estrutura do Projeto
      
```
Projeto/
│
├── dashboard_sistema/
│   └── app.py                   # Aplicação principal (Estoque + Vendas + Compras)
│
├── dados/
│   ├── FCD_estoque.csv          # Base de estoque
│   ├── FCD_produtos.csv         # Base de produtos
│   ├── FCD_vendas.csv           # Base de vendas
│   ├── FCD_clientes.csv         # Base de clientes
│   └── FCD_compras.csv          # Base de compras e fornecedores
│
├── README.md                    # Documentação do projeto
│
└── venv/                        # Ambiente virtual (não versionado)
```

## ⚙️ Como Executar o Projeto

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Vandielson/projeto_fundamentos_de_ciencias_de_dados.git


2. **Entre na pasta do projeto:**
   ```bash
   cd Projeto


3. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   venv\Scripts\activate


4. **Instale as dependências:**
   ```bash
   pip install streamlit pandas matplotlib seaborn


5. **Execute o aplicativo:**
    ```bash
    streamlit run dashboard_sistema/app.py


6. **Abra no navegador:**

http://localhost:8501

## 👤 Autor

- Vandielson Tenório Feitosa de Assis
- Graduando em Ciência da Computação
- 📧 vandielson.tenorio@ufape.com.br
- 💼 GitHub: https://github.com/Vandielson

## 📄 Licença

Este projeto é de uso educacional, desenvolvido para fins acadêmicos na disciplina Fundamentos em Ciência de Dados.

