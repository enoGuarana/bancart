# sistema/aba_balcao.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
from sistema.config import CORES, DB_NAME

class AbaBalcao(tk.Frame):
    def __init__(self, parent, app_principal):
        super().__init__(parent, bg=CORES['fundo'])
        self.app = app_principal
        self.carrinho_avulso = []
        self.produto_selecionado_id = None 
        self.lista_produtos_cache = []     
        self.montar_interface()

    def montar_interface(self):
        fr_topo = tk.Frame(self, bg=CORES['painel'], pady=10); fr_topo.pack(fill='x')
        tk.Label(fr_topo, text="BALCÃO RÁPIDO", font=('Arial', 18, 'bold'), fg=CORES['laranja'], bg=CORES['painel']).pack()
        
        fr_inp = tk.Frame(fr_topo, bg=CORES['painel']); fr_inp.pack(pady=5)
        fr_busca_hibrida = tk.Frame(fr_inp, bg=CORES['painel'])
        fr_busca_hibrida.pack(side='left', padx=5)
        
        self.ent_busca_prod = tk.Entry(fr_busca_hibrida, font=('Arial', 12), width=28, bg='white', fg='gray')
        self.ent_busca_prod.grid(row=0, column=0, sticky='ew')
        self.ent_busca_prod.insert(0, "Digite o nome ou código...")
        
        self.ent_busca_prod.bind("<FocusIn>", self.limpar_placeholder_busca)
        self.ent_busca_prod.bind("<FocusOut>", self.restaurar_placeholder_busca)
        self.ent_busca_prod.bind("<KeyRelease>", self.filtrar_produtos_busca)
        self.ent_busca_prod.bind("<Return>", self.selecionar_produto_por_busca)
        self.ent_busca_prod.bind("<Down>", lambda e: self.list_sugestoes.focus_set() if self.list_sugestoes.winfo_viewable() else None)
        
        self.btn_ver_todos = tk.Button(fr_busca_hibrida, text="🔽", font=('Arial', 8), bg='white', fg='black', bd=1, relief='flat', command=self.exibir_lista_completa)
        self.btn_ver_todos.grid(row=0, column=1, sticky='ns')
        
        self.ent_qtd_avulso = tk.Entry(fr_inp, width=5, font=('Arial', 12), justify='center')
        self.ent_qtd_avulso.insert(0, "1")
        self.ent_qtd_avulso.pack(side='left', padx=5)
        
        tk.Button(fr_inp, text="LANÇAR", bg=CORES['azul'], fg='white', font=('Arial', 10, 'bold'), command=self.add_carrinho_avulso).pack(side='left', padx=10)
        
        self.list_sugestoes = tk.Listbox(fr_topo, font=('Arial', 10), height=5, bg='white', fg='black', selectbackground=CORES['azul'], selectforeground='white', activestyle='none')
        self.list_sugestoes.pack(fill='x', padx=30, pady=2)
        
        self.list_sugestoes.bind("<<ListboxSelect>>", self.selecionar_produto_lista)
        self.list_sugestoes.bind("<Motion>", self.efeito_hover_listbox)
        self.list_sugestoes.bind("<Return>", self.selecionar_produto_lista)
        self.list_sugestoes.pack_forget() 

        self.tree_avulso = ttk.Treeview(self, columns=('Prod','Qtd','Total'), show='headings', height=10)
        self.tree_avulso.heading('Prod', text='Produto'); self.tree_avulso.column('Prod', width=250, anchor='w')
        self.tree_avulso.heading('Qtd', text='Qtd'); self.tree_avulso.column('Qtd', width=70, anchor='center')
        self.tree_avulso.heading('Total', text='Total'); self.tree_avulso.column('Total', width=100, anchor='center')
        self.tree_avulso.pack(fill='both', expand=True, padx=10, pady=5)
        
        tk.Button(self, text="🗑️ Limpar Carrinho", font=('Arial', 9), command=self.limpar_avulso).pack(pady=2)
        
        fr_base = tk.Frame(self, bg=CORES['painel'], pady=10); fr_base.pack(fill='x', padx=10, pady=10)
        self.lbl_total_avulso = tk.Label(fr_base, text="TOTAL: R$ 0.00", font=('Arial', 24, 'bold'), fg=CORES['verde'], bg=CORES['painel'])
        self.lbl_total_avulso.pack(side='left', padx=20)
        
        fr_pag = tk.Frame(fr_base, bg=CORES['painel']); fr_pag.pack(side='right', padx=20)
        self.cb_pag_avulso = ttk.Combobox(fr_pag, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"], font=('Arial', 10), state="readonly")
        self.cb_pag_avulso.current(0); self.cb_pag_avulso.pack(pady=2)
        
        tk.Button(fr_pag, text="FINALIZAR VENDA", bg=CORES['verde'], fg='white', font=('Arial', 12, 'bold'), command=self.finalizar_avulso).pack(pady=3, fill='x')
        tk.Button(fr_pag, text="🎁 CORTESIA FUNC.", bg=CORES['azul'], fg='white', font=('Arial', 11, 'bold'), command=self.finalizar_cortesia).pack(pady=3, fill='x')

    def atualizar_combobox(self, lista_cb):
        self.lista_produtos_cache = []
        produtos_por_id = {item[0]: item for item in self.app.lista_produtos_cache}
        for texto_completo in lista_cb:
            try:
                produto_id = int(texto_completo.split(' - ', 1)[0])
                produto = produtos_por_id.get(produto_id)
                if produto:
                    nome = str(produto[1])
                    codigo = str(produto[4]).strip() if produto[4] is not None else ""
                else:
                    nome = texto_completo.split(' - ', 1)[1].split(' | ', 1)[0]
                    codigo = ""

                texto_exibicao = texto_completo
                if codigo:
                    texto_exibicao += f" | Cód. barras: {codigo}"

                self.lista_produtos_cache.append({
                    'id': produto_id,
                    'nome': nome,
                    'codigo': codigo,
                    'texto_completo': texto_exibicao
                })
            except (ValueError, IndexError):
                pass

    def limpar_placeholder_busca(self, event):
        if self.ent_busca_prod.get() == "Digite o nome ou código...":
            self.ent_busca_prod.delete(0, tk.END); self.ent_busca_prod.config(fg='black')

    def restaurar_placeholder_busca(self, event):
        if not self.ent_busca_prod.get().strip():
            self.ent_busca_prod.delete(0, tk.END); self.ent_busca_prod.insert(0, "Digite o nome ou código..."); self.ent_busca_prod.config(fg='gray')

    def efeito_hover_listbox(self, event):
        index = self.list_sugestoes.nearest(event.y)
        if index >= 0: self.list_sugestoes.selection_clear(0, tk.END); self.list_sugestoes.selection_set(index); self.list_sugestoes.activate(index)

    def exibir_lista_completa(self):
        if self.list_sugestoes.winfo_viewable(): self.list_sugestoes.pack_forget(); return
        self.limpar_placeholder_busca(None)
        self.list_sugestoes.delete(0, tk.END)
        if self.lista_produtos_cache:
            self.list_sugestoes.pack(fill='x', padx=30, pady=2)
            for prod in self.lista_produtos_cache: self.list_sugestoes.insert(tk.END, prod['texto_completo'])

    def filtrar_produtos_busca(self, event):
        if event.keysym in ["Up", "Down", "Left", "Right", "Return"]: return
        termo = self.ent_busca_prod.get().strip().lower()
        if not termo or termo == "digite o nome ou código...": self.list_sugestoes.pack_forget(); self.produto_selecionado_id = None; return
        resultados = [
            p for p in self.lista_produtos_cache
            if termo in p['nome'].lower()
            or termo in p.get('codigo', '').lower()
            or termo in str(p['id'])
        ]
        self.list_sugestoes.delete(0, tk.END)
        if resultados:
            self.list_sugestoes.pack(fill='x', padx=30, pady=2)
            for prod in resultados: self.list_sugestoes.insert(tk.END, prod['texto_completo'])
        else: self.list_sugestoes.pack_forget(); self.produto_selecionado_id = None

    def selecionar_produto_por_busca(self, event=None):
        """Seleciona pelo código bipado ou pelo único resultado da pesquisa."""
        termo = self.ent_busca_prod.get().strip().lower()
        if not termo:
            return "break"

        correspondencias_exatas = [
            p for p in self.lista_produtos_cache
            if p.get('codigo', '').lower() == termo
        ]
        if correspondencias_exatas:
            self.definir_produto_selecionado(correspondencias_exatas[0])
            return "break"

        resultados = [
            p for p in self.lista_produtos_cache
            if termo in p['nome'].lower()
            or termo in p.get('codigo', '').lower()
            or termo in str(p['id'])
        ]
        if len(resultados) == 1:
            self.definir_produto_selecionado(resultados[0])
        return "break"

    def definir_produto_selecionado(self, produto):
        self.produto_selecionado_id = produto['id']
        self.ent_busca_prod.config(fg='black')
        self.ent_busca_prod.delete(0, tk.END)
        self.ent_busca_prod.insert(0, produto['nome'])
        self.list_sugestoes.pack_forget()
        self.ent_qtd_avulso.focus_set()
        self.ent_qtd_avulso.selection_range(0, tk.END)

    def selecionar_produto_lista(self, event):
        selecao = self.list_sugestoes.curselection()
        if not selecao: return
        texto_produto = self.list_sugestoes.get(selecao[0])
        try:
            pid = int(texto_produto.split(' - ')[0])
            produto = next(p for p in self.lista_produtos_cache if p['id'] == pid)
            self.definir_produto_selecionado(produto)
        except Exception as e: print(e)

    # --- REQUISITO 2: POPUP EXCLUSIVO DE SELEÇÃO DE ESPETO ---
    def abrir_selecao_espeto_balcao(self):
        janela_esp = tk.Toplevel(self); janela_esp.title("Componentes da Jantinha"); janela_esp.geometry("380x300"); janela_esp.configure(bg=CORES['painel']); janela_esp.resizable(False, False); janela_esp.transient(self)
        tk.Label(janela_esp, text="🍢 SELECIONE O ESPETO DA JANTINHA", font=('Arial', 11, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=8)
        ent_busca = tk.Entry(janela_esp, font=('Arial', 11), width=25); ent_busca.insert(0, "ESPETO"); ent_busca.pack(pady=4)
        list_esp = tk.Listbox(janela_esp, font=('Arial', 10), height=6, bg='white', fg='black', selectbackground=CORES['azul']); list_esp.pack(fill='both', expand=True, padx=15, pady=5)
        espeto_id_selecionado = [None]

        def filtrar_espetos(event=None):
            termo = ent_busca.get().strip().lower()
            list_esp.delete(0, tk.END)
            for p in self.lista_produtos_cache:
                if "espeto" in p['nome'].lower() and (not termo or termo in p['nome'].lower()): list_esp.insert(tk.END, p['texto_completo'])
        ent_busca.bind("<KeyRelease>", filtrar_espetos); filtrar_espetos()

        def confirmar_espeto():
            sel = list_esp.curselection()
            if not sel: messagebox.showwarning("Aviso", "Escolha o espeto!", parent=janela_esp); return
            espeto_id_selecionado[0] = int(list_esp.get(sel[0]).split(' - ')[0]); janela_esp.destroy()

        tk.Button(janela_esp, text="VINCULAR AO PEDIDO", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=confirmar_espeto).pack(pady=10)
        janela_esp.update(); janela_esp.grab_set()
        self.wait_window(janela_esp)
        return espeto_id_selecionado[0]

    def add_carrinho_avulso(self):
        if not self.produto_selecionado_id: messagebox.showwarning("Aviso", "Selecione um produto."); return
        try:
            qtd = int(self.ent_qtd_avulso.get())
            pid = self.produto_selecionado_id
            conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
            res = cursor.execute("SELECT nome, preco, estoque FROM produtos WHERE id=?", (pid,)).fetchone()
            
            if res[2] < qtd: messagebox.showerror("Erro", f"Estoque insuficiente! Disponível: {res[2]}"); conn.close(); return
            
            nome_final = res[0]
            espeto_id = None
            if "jantinha" in res[0].lower():
                espeto_id = self.abrir_selecao_espeto_balcao()
                if not espeto_id: conn.close(); return
                esp_res = cursor.execute("SELECT nome, estoque FROM produtos WHERE id=?", (espeto_id,)).fetchone()
                if esp_res[1] < qtd: messagebox.showerror("Erro", f"Sem estoque do {esp_res[0]}!"); conn.close(); return
                nome_final = f"{res[0]} (+ {esp_res[0]})"

            conn.close()
            # O carrinho armazena temporariamente a estrutura e o espeto_id para dar a baixa real apenas no ato do pagamento
            self.carrinho_avulso.append({'id': pid, 'nome': nome_final, 'qtd': qtd, 'tot': res[1] * qtd, 'espeto_id': espeto_id})
            self.atualizar_avulso()
            
            self.ent_busca_prod.delete(0, tk.END); self.ent_busca_prod.insert(0, "Digite o nome ou código..."); self.ent_busca_prod.config(fg='gray')
            self.ent_qtd_avulso.delete(0, tk.END); self.ent_qtd_avulso.insert(0, "1"); self.produto_selecionado_id = None
        except Exception as e: print(e)

    def atualizar_avulso(self):
        self.tree_avulso.delete(*self.tree_avulso.get_children()); geral = 0
        for i in self.carrinho_avulso: self.tree_avulso.insert('', 'end', values=(i['nome'], i['qtd'], f"{i['tot']:.2f}")); geral += i['tot']
        self.lbl_total_avulso.config(text=f"TOTAL: R$ {geral:.2f}")

    def limpar_avulso(self): 
        self.carrinho_avulso = []; self.produto_selecionado_id = None
        self.ent_busca_prod.delete(0, tk.END); self.ent_busca_prod.insert(0, "Digite o nome ou código..."); self.ent_busca_prod.config(fg='gray')
        self.atualizar_avulso()

    def finalizar_avulso(self):
        if not self.carrinho_avulso: return
        total_venda = sum(item['tot'] for item in self.carrinho_avulso)
        saldo_restante = [total_venda]
        pagamentos_parciais = []

        janela_desc = tk.Toplevel(self)
        janela_desc.title("Fechamento - Balcão")
        janela_desc.geometry("420x380")
        janela_desc.configure(bg=CORES['painel'])
        janela_desc.resizable(False, False)
        janela_desc.transient(self)

        def efetivar_venda_balcao(desconto, forma_pgto_final):
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                valor_final = saldo_restante[0] - desconto
                formas_usadas = [forma for _, forma in pagamentos_parciais]
                if valor_final > 0.01 or not formas_usadas:
                    formas_usadas.append(forma_pgto_final)
                pagamento_resumo = " + ".join(dict.fromkeys(formas_usadas))
                c.execute("INSERT INTO atendimentos (mesa_id, data_abertura, data_fechamento, desconto, pagamento, status) VALUES (?,?,?,?,?,?)", (0, dt_agora, dt_agora, desconto, pagamento_resumo, 'FECHADO'))
                id_balcao_gerado = c.lastrowid
                hora_txt = dt_agora.split(' ')[1]
                venda_dividida = bool(pagamentos_parciais)

                for item in self.carrinho_avulso:
                    # Se houver espeto amarrado na jantinha, realiza a baixa do estoque dele
                    if item.get('espeto_id'):
                        c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item['qtd'], item['espeto_id']))

                    c.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_balcao_gerado, item['nome'], item['qtd'], item['tot']))
                    c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
                    
                    # --- REQUISITO 1: GRAVAÇÃO EM TABELA DE RELATÓRIO INDIVIDUAL DO BALCÃO ---
                    c.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_txt, "BALCÃO", item['nome'], item['qtd'], 0.0 if venda_dividida else item['tot'], "DETALHE" if venda_dividida else forma_pgto_final)
                    )

                for valor_pago, forma_pgto in pagamentos_parciais:
                    nome_parcial = f"PAG. PARCIAL ({forma_pgto})"
                    c.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_balcao_gerado, nome_parcial, 1, 0.0))
                    c.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_txt, "BALCÃO", nome_parcial, 1, valor_pago, forma_pgto)
                    )

                if venda_dividida and valor_final > 0.01:
                    c.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_txt, "BALCÃO", f"SALDO FINAL ({forma_pgto_final})", 1, valor_final, forma_pgto_final)
                    )

                if desconto > 0:
                    c.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_balcao_gerado, "DESCONTO MANUAL", 1, -desconto))
                    c.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_txt, "BALCÃO", "DESCONTO MANUAL", 1, 0.0 if venda_dividida else -desconto, "DETALHE" if venda_dividida else forma_pgto_final)
                    )
                
                conn.commit()
                janela_desc.destroy()
                self.limpar_avulso(); self.app.atualizar_todos_produtos(); self.app.aba_caixa.carregar_historico()
                if hasattr(self, 'emitir_recibo_balcao_pdf') and messagebox.askyesno("Venda Balcão", "Venda realizada!\nDeseja o PDF?"):
                    self.emitir_recibo_balcao_pdf(id_balcao_gerado, total_venda - desconto)
            except Exception as e: conn.rollback(); messagebox.showerror("Erro", str(e))
            finally: conn.close()

        def solicitar_troco_dinheiro(valor_a_cobrar, funcao_sucesso):
            janela_troco = tk.Toplevel(janela_desc); janela_troco.title("Calculadora de Troco"); janela_troco.geometry("320x200"); janela_troco.configure(bg=CORES['painel']); janela_troco.resizable(False, False); janela_troco.transient(janela_desc)
            tk.Label(janela_troco, text="💵 PAGAMENTO EM DINHEIRO", font=('Arial', 11, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
            tk.Label(janela_troco, text=f"Valor a Pagar: R$ {valor_a_cobrar:.2f}", font=('Arial', 11), bg=CORES['painel'], fg='white').pack()
            ent_recebido = tk.Entry(janela_troco, font=('Arial', 12), width=15, justify='center'); ent_recebido.insert(0, f"{valor_a_cobrar:.2f}"); ent_recebido.pack(); ent_recebido.focus_set(); ent_recebido.selection_range(0, tk.END)
            lbl_troco = tk.Label(janela_troco, text="TROCO: R$ 0.00", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['verde']); lbl_troco.pack(pady=5)
            def calcular(event=None):
                try:
                    recebido = float(ent_recebido.get().replace(',', '.'))
                    troco = recebido - valor_a_cobrar
                    lbl_troco.config(text=f"TROCO: R$ {max(0.0, troco):.2f}" if troco >= 0 else "VALOR INSUFICIENTE", fg=CORES['verde'] if troco >= 0 else CORES['vermelho'])
                except ValueError: lbl_troco.config(text="VALOR INVÁLIDO", fg=CORES['vermelho'])
            ent_recebido.bind("<KeyRelease>", calcular)
            def confirmar_pgto():
                try:
                    recebido = float(ent_recebido.get().replace(',', '.'))
                    if recebido < valor_a_cobrar: messagebox.showerror("Erro", "Valor menor que cobrado!", parent=janela_troco); return
                    troco = recebido - valor_a_cobrar
                except ValueError: return
                if troco > 0: messagebox.showinfo("Troco", f"Devolver: R$ {troco:.2f}", parent=janela_troco)
                janela_troco.destroy(); funcao_sucesso()
            fr_bnt = tk.Frame(janela_troco, bg=CORES['painel']); fr_bnt.pack(pady=10)
            tk.Button(fr_bnt, text="PAGO EXATO", bg=CORES['busca'], fg='white', font=('Arial', 9, 'bold'), command=lambda: [ent_recebido.delete(0, tk.END), ent_recebido.insert(0, str(valor_a_cobrar)), confirmar_pgto()]).pack(side='left', padx=5)
            tk.Button(fr_bnt, text="CONFIRMAR", bg=CORES['verde'], fg='white', font=('Arial', 9, 'bold'), command=confirmar_pgto).pack(side='left', padx=5)
            janela_troco.update(); janela_troco.grab_set()

        def salvar_pagamento_parcial(valor_pago, forma_pgto):
            pagamentos_parciais.append((valor_pago, forma_pgto))
            saldo_restante[0] -= valor_pago
            lbl_saldo.config(text=f"SALDO RESTANTE: R$ {saldo_restante[0]:.2f}", fg=CORES['vermelho'] if saldo_restante[0] > 0.01 else CORES['verde'])
            ent_valor_pagar.delete(0, tk.END); ent_valor_pagar.insert(0, f"{saldo_restante[0]:.2f}")
            if saldo_restante[0] <= 0.01:
                finalizar_totalmente(deve_perguntar=False)
            else:
                messagebox.showinfo("Sucesso", f"Recebido R$ {valor_pago:.2f}!", parent=janela_desc)

        def receber_pagamento_parcial():
            try:
                valor_pago = float(ent_valor_pagar.get().replace(',', '.'))
                if valor_pago <= 0 or valor_pago > saldo_restante[0] + 0.01: raise ValueError
            except ValueError: messagebox.showerror("Erro", "Valor inserido inválido.", parent=janela_desc); return
            forma_pgto = cb_forma_parcial.get()
            if forma_pgto == "DINHEIRO": solicitar_troco_dinheiro(valor_pago, lambda: salvar_pagamento_parcial(valor_pago, forma_pgto))
            elif messagebox.askyesno("Confirmar", f"Receber R$ {valor_pago:.2f} no {forma_pgto}?", parent=janela_desc):
                salvar_pagamento_parcial(valor_pago, forma_pgto)

        def finalizar_totalmente(deve_perguntar=True):
            try:
                desconto = float(ent_desc.get().replace(',', '.'))
                if desconto < 0 or desconto > saldo_restante[0]: raise ValueError
            except ValueError: messagebox.showerror("Erro", "Valor de desconto inválido.", parent=janela_desc); return
            total_final = saldo_restante[0] - desconto
            forma_pgto_final = self.cb_pag_avulso.get()
            if total_final <= 0.01:
                efetivar_venda_balcao(desconto, forma_pgto_final)
            elif forma_pgto_final == "DINHEIRO":
                solicitar_troco_dinheiro(total_final, lambda: efetivar_venda_balcao(desconto, forma_pgto_final))
            else:
                texto = f"Total Restante: R$ {saldo_restante[0]:.2f}\nDesconto: R$ {desconto:.2f}\nValor Final: R$ {total_final:.2f}\nFechar com {forma_pgto_final}?"
                if not deve_perguntar or messagebox.askyesno("Confirmar", texto, parent=janela_desc): efetivar_venda_balcao(desconto, forma_pgto_final)

        def fechar_janela():
            if pagamentos_parciais:
                messagebox.showwarning("Pagamento em andamento", "Finalize a venda antes de fechar: há pagamentos parciais recebidos.", parent=janela_desc)
                return
            janela_desc.destroy()

        tk.Label(janela_desc, text="FECHAMENTO DO BALCÃO", font=('Arial', 13, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        lbl_saldo = tk.Label(janela_desc, text=f"SALDO RESTANTE: R$ {total_venda:.2f}", font=('Arial', 14, 'bold'), bg=CORES['painel'], fg=CORES['verde']); lbl_saldo.pack(pady=5)
        fr_divisao = tk.LabelFrame(janela_desc, text=" Receber Pagamento Parcial (Dividir Conta) ", bg=CORES['painel'], fg='white', font=('Arial', 10, 'bold'), padx=10, pady=10); fr_divisao.pack(fill='x', padx=15, pady=5)
        tk.Label(fr_divisao, text="Valor a pagar agora (R$):", bg=CORES['painel'], fg='white').grid(row=0, column=0, sticky='w', pady=2)
        ent_valor_pagar = tk.Entry(fr_divisao, font=('Arial', 11), width=14, justify='center'); ent_valor_pagar.insert(0, f"{total_venda:.2f}"); ent_valor_pagar.grid(row=0, column=1, pady=2, padx=5)
        tk.Label(fr_divisao, text="Forma de Pagamento:", bg=CORES['painel'], fg='white').grid(row=1, column=0, sticky='w', pady=2)
        cb_forma_parcial = ttk.Combobox(fr_divisao, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"], width=12, state="readonly"); cb_forma_parcial.current(0); cb_forma_parcial.grid(row=1, column=1, pady=2, padx=5)
        tk.Button(fr_divisao, text="RECEBER PARTE", bg=CORES['azul'], fg='white', font=('Arial', 9, 'bold'), command=receber_pagamento_parcial).grid(row=0, column=2, rowspan=2, padx=10, ipady=4)
        fr_total = tk.LabelFrame(janela_desc, text=" Encerrar Saldo Restante / Aplicar Desconto ", bg=CORES['painel'], fg='white', font=('Arial', 10, 'bold'), padx=10, pady=10); fr_total.pack(fill='x', padx=15, pady=10)
        tk.Label(fr_total, text="Conceder Desconto (R$):", bg=CORES['painel'], fg='white').pack(side='left', padx=5)
        ent_desc = tk.Entry(fr_total, font=('Arial', 11), width=12, justify='center'); ent_desc.insert(0, "0.00"); ent_desc.pack(side='left', padx=5)
        tk.Button(fr_total, text="FECHAR CONTA", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=lambda: finalizar_totalmente(deve_perguntar=True)).pack(side='right', padx=5, ipady=2)
        janela_desc.protocol("WM_DELETE_WINDOW", fechar_janela)
        janela_desc.update(); janela_desc.grab_set(); ent_valor_pagar.focus_set(); ent_valor_pagar.selection_range(0, tk.END)

    def finalizar_cortesia(self):
        if not self.carrinho_avulso: return
        janela_nome = tk.Toplevel(self); janela_nome.title("Nome"); janela_nome.geometry("350x180"); janela_nome.configure(bg=CORES['painel']); janela_nome.transient(self)
        tk.Label(janela_nome, text="Nome do Funcionário:", bg=CORES['painel'], fg='white').pack(pady=10)
        ent_nome_func = tk.Entry(janela_nome, font=('Arial', 11), width=25, justify='center'); ent_nome_func.pack(); ent_nome_func.focus_set()

        def confirmar_gravacao_cortesia():
            nome_recebedor = ent_nome_func.get().strip().upper()
            if not nome_recebedor: messagebox.showerror("Erro", "Nome obrigatório!", parent=janela_nome); return
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                c.execute("INSERT INTO atendimentos (mesa_id, data_abertura, data_fechamento, desconto, pagamento, status) VALUES (?,?,?,?,?,?)", (0, dt_agora, dt_agora, 0.0, f"CORTESIA ({nome_recebedor})", 'FECHADO'))
                id_cortesia_gerado = c.lastrowid
                hora_txt = dt_agora.split(' ')[1]

                for item in self.carrinho_avulso:
                    if item.get('espeto_id'):
                        c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item['qtd'], item['espeto_id']))
                    c.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_cortesia_gerado, f"[CORTESIA] {item['nome']}", item['qtd'], 0.00))
                    c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
                    
                    # --- REQUISITO 1: GRAVAÇÃO EM TABELA DE RELATÓRIO INDIVIDUAL PARA CORTESIA ---
                    c.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_txt, "BALCÃO", f"[CORTESIA] {item['nome']}", item['qtd'], 0.00, f"CORTESIA ({nome_recebedor})")
                    )
                conn.commit(); janela_nome.destroy()
                self.limpar_avulso(); self.app.atualizar_todos_produtos(); self.app.aba_caixa.carregar_historico()
                if messagebox.askyesno("Cortesia", "Gravada!\nDeseja o PDF?"): self.emitir_recibo_balcao_pdf(id_cortesia_gerado, 0.00)
            except Exception as e: conn.rollback(); messagebox.showerror("Erro", str(e), parent=janela_nome)
            finally: conn.close()

        tk.Button(janela_nome, text="LIBERAR CORTESIA", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=confirmar_gravacao_cortesia).pack(pady=15)
        janela_nome.update(); janela_nome.grab_set()
