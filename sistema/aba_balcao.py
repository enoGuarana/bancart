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
        for item in lista_cb:
            try:
                partes = item.split(' - ')
                self.lista_produtos_cache.append({'id': int(partes[0]), 'nome': partes[1], 'texto_completo': item})
            except: pass

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
        resultados = [p for p in self.lista_produtos_cache if termo in p['nome'].lower() or termo in str(p['id'])]
        self.list_sugestoes.delete(0, tk.END)
        if resultados:
            self.list_sugestoes.pack(fill='x', padx=30, pady=2)
            for prod in resultados: self.list_sugestoes.insert(tk.END, prod['texto_completo'])
        else: self.list_sugestoes.pack_forget(); self.produto_selecionado_id = None

    def selecionar_produto_lista(self, event):
        selecao = self.list_sugestoes.curselection()
        if not selecao: return
        texto_produto = self.list_sugestoes.get(selecao[0])
        try:
            pid = int(texto_produto.split(' - ')[0])
            self.produto_selecionado_id = pid
            self.ent_busca_prod.config(fg='black')
            self.ent_busca_prod.delete(0, tk.END)
            self.ent_busca_prod.insert(0, texto_produto.split(' - ')[1])
            self.list_sugestoes.pack_forget()
            self.ent_qtd_avulso.focus_set(); self.ent_qtd_avulso.selection_range(0, tk.END)
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
        forma_pgto = self.cb_pag_avulso.get()

        def efetivar_venda_balcao():
            conn = sqlite3.connect(DB_NAME); c = conn.cursor(); dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                c.execute("INSERT INTO atendimentos (mesa_id, data_abertura, data_fechamento, desconto, pagamento, status) VALUES (?,?,?,?,?,?)", (0, dt_agora, dt_agora, 0.0, forma_pgto, 'FECHADO'))
                id_balcao_gerado = c.lastrowid
                hora_txt = dt_agora.split(' ')[1]

                for item in self.carrinho_avulso:
                    # Se houver espeto amarrado na jantinha, realiza a baixa do estoque dele
                    if item.get('espeto_id'):
                        c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item['qtd'], item['espeto_id']))

                    c.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_balcao_gerado, item['nome'], item['qtd'], item['tot']))
                    c.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (item['qtd'], item['id']))
                    
                    # --- REQUISITO 1: GRAVAÇÃO EM TABELA DE RELATÓRIO INDIVIDUAL DO BALCÃO ---
                    c.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_txt, "BALCÃO", item['nome'], item['qtd'], item['tot'], forma_pgto)
                    )
                
                conn.commit()
                self.limpar_avulso(); self.app.atualizar_todos_produtos(); self.app.aba_caixa.carregar_historico()
                if messagebox.askyesno("Venda Balcão", "Venda realizada!\nDeseja o PDF?"): self.emitir_recibo_balcao_pdf(id_balcao_gerado, total_venda)
            except Exception as e: conn.rollback(); messagebox.showerror("Erro", str(e))
            finally: conn.close()

        if forma_pgto == "DINHEIRO":
            janela_troco = tk.Toplevel(self); janela_troco.title("Troco"); janela_troco.geometry("320x200"); janela_troco.configure(bg=CORES['painel']); janela_troco.transient(self)
            tk.Label(janela_troco, text="💵 VENDA EM DINHEIRO", font=('Arial', 11, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
            tk.Label(janela_troco, text=f"Total: R$ {total_venda:.2f}", font=('Arial', 11), bg=CORES['painel'], fg='white').pack()
            ent_recebido = tk.Entry(janela_troco, font=('Arial', 12), width=15, justify='center'); ent_recebido.insert(0, f"{total_venda:.2f}"); ent_recebido.pack(); ent_recebido.focus_set(); ent_recebido.selection_range(0, tk.END)
            lbl_troco = tk.Label(janela_troco, text="TROCO: R$ 0.00", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['verde']); lbl_troco.pack(pady=5)
            def calcular_troco(event=None):
                try:
                    recebido = float(ent_recebido.get().replace(',', '.'))
                    troco = recebido - total_venda
                    lbl_troco.config(text=f"TROCO: R$ {max(0.0, troco):.2f}" if troco >= 0 else "VALOR INSUFICIENTE", fg=CORES['verde'] if troco >= 0 else CORES['vermelho'])
                except ValueError: lbl_troco.config(text="VALOR INVÁLIDO", fg=CORES['vermelho'])
            ent_recebido.bind("<KeyRelease>", calcular_troco)
            def confirmar_e_fechar():
                try:
                    recebido = float(ent_recebido.get().replace(',', '.'))
                    if recebido < total_venda: messagebox.showerror("Erro", "Valor insuficiente!", parent=janela_troco); return
                    troco = recebido - total_venda
                except ValueError: return
                if troco > 0: messagebox.showinfo("Troco", f"Troco: R$ {troco:.2f}", parent=janela_troco)
                janela_troco.destroy(); efetivar_venda_balcao()
            fr_bnt = tk.Frame(janela_troco, bg=CORES['painel']); fr_bnt.pack(pady=10)
            tk.Button(fr_bnt, text="PAGO EXATO", bg=CORES['busca'], fg='white', font=('Arial', 9, 'bold'), command=lambda: [ent_recebido.delete(0, tk.END), ent_recebido.insert(0, str(total_venda)), confirmar_e_fechar()]).pack(side='left', padx=5)
            tk.Button(fr_bnt, text="FINALIZAR", bg=CORES['verde'], fg='white', font=('Arial', 9, 'bold'), command=confirmar_e_fechar).pack(side='left', padx=5)
            janela_troco.update(); janela_troco.grab_set()
        else:
            if messagebox.askyesno("Confirmar", "Finalizar com cartão/pix?"): efetivar_venda_balcao()

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