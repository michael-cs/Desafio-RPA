# Desafio RPA - Sauce Demo → Fakturama

Exercício de aula combinando as duas grandes famílias de automação RPA:
**web** (seletor/DOM, via Selenium/BotCity WebBot) e **desktop** (reconhecimento
de imagem, via BotCity DesktopBot). O bot raspa um comprador fake e o catálogo
completo de uma loja de teste ([Sauce Demo](https://www.saucedemo.com/)) e
replica esses dados como cadastro mestre no [Fakturama](https://www.fakturama.info/)
(software desktop de faturamento).

Construído sobre o framework BeaPro (BotCity Enterprise Automation): state
management, exceções tipadas (`BusinessException`/`SystemException`/`InterruptException`),
datasource CSV, e logging/relatórios duplos (arquivo local + BotCity Maestro Orchestrator).

📄 Descritivo completo da tarefa (objetivo, fluxo, entregáveis obrigatórios): [docs/Descritivo_Tarefa.pdf](docs/Descritivo_Tarefa.pdf).

## O que o bot faz

1. Gera um comprador fake brasileiro em [fakenamegenerator.com](https://www.fakenamegenerator.com/gen-random-br-br.php)
2. Loga no Sauce Demo e raspa o catálogo completo (6 produtos) → `assets/item_list.csv`
3. Cadastra o comprador no Fakturama
4. Para cada um dos 6 produtos raspados: cadastra como um novo produto no Fakturama, reportando sucesso/erro individualmente

**Critério de validação**: comparar a contagem/nomes em `assets/item_list.csv` com a lista de Produtos do Fakturama após a execução — se bateu, a automação funcionou ponta a ponta.

## Estrutura

```
bot.py                    # orquestrador principal
framework/                 # state, exceções, logging, datasources, initialize/finalize
ecommerce/                 # lógica de negócio web (fake_contact, sauce_demo)
fakturama_desktop/          # lógica de negócio desktop (Fakturama via reconhecimento de imagem)
assets/images/               # imagens usadas pelo DesktopBot para localizar elementos do Fakturama
```

## Instalação

```bash
pip install -r requirements.txt
```

Requer o [Fakturama](https://www.fakturama.info/) instalado localmente (caminho configurado em `framework/config.py::FAKTURAMA_EXE_PATH`).

## Execução

```bash
python bot.py
```

Sem um arquivo `.env`, o bot roda em **test mode** (sem conta BotCity, sem upload pro Orchestrator) —
**essa conexão não é obrigatória para o desafio**. Log e evidências são salvos normalmente na pasta
local `output/` de qualquer forma. Para rodar com integração ao BotCity Maestro, copie `.env.example`
para `.env` e preencha suas credenciais.

## Saída (`output/`)

Independentemente de estar conectado ao Maestro ou não, a pasta `output/` deve conter, ao final de
uma execução bem-sucedida:

- `contact_list.csv` / `item_list.csv` — dados raspados do comprador e do catálogo (**obrigatório**)
- `fakturama_contact_registered.png` — evidência do cadastro do comprador no Fakturama (**obrigatório**)
- `fakturama_products_list.png` — evidência da lista completa de produtos no Fakturama (**obrigatório**)
- `Log_BotCity_...log` — log completo da execução
- `CSV_BotCity_...csv` — status (sucesso/erro) de cada um dos 6 produtos cadastrados
- `temp/error-*.png` — screenshot automático em caso de erro
