# sistema/aba_mesas.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
from sistema.config import CORES, DB_NAME

class AbaMesas(tk.Frame):
    def __init__(self, parent, app_principal):
        super().__init__(parent, bg=CORES['fundo'])
        self.app = app_principal  
        self.mesa_atual = None
        self.atendimento_id_actual = None 
        self.produto_selecionado_id = None 
        self.lista_produtos_cache = []     
        self.nomes_mesas = {i: f"MESA {i:02d}" for i in range(1, 21)}
        self.montar_interface()
        
    def montar_interface(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1) 
        self.columnconfigure(1, weight=1) 

        fr_btn = tk.Frame(self, bg=CORES['painel'], bd=2, relief='groove')
        fr_btn.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        tk.Label(fr_btn, text="MAPA DE MESAS", bg=CORES['painel'], fg='white', font=('Arial', 12, 'bold')).pack(pady=10, fill='x')
        
        fr_grid = tk.Frame(fr_btn, bg=CORES['painel'])
        fr_grid.pack(expand=True, fill='both', padx=10, pady=5)
        for r in range(5): fr_grid.rowconfigure(r, weight=1)
        for c in range(4): fr_grid.columnconfigure(c, weight=1)

        self.btns_mesa = {}
        for i in range(1, 21):
            btn = tk.Button(fr_grid, text=self.nomes_mesas[i], bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=lambda m=i: self.selecionar_mesa(m))
            r, c = divmod(i-1, 4)
            btn.grid(row=r, column=c, padx=4, pady=4, sticky='nsew')
            self.btns_mesa[i] = btn
        
        fr_det = tk.Frame(self, bg=CORES['fundo'])
        fr_det.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        
        fr_topo_det = tk.Frame(fr_det, bg=CORES['fundo'])
        fr_topo_det.pack(fill='x', pady=5)
        self.lbl_mesa_sel = tk.Label(fr_topo_det, text="Selecione uma Mesa", font=('Arial', 14, 'bold'), fg=CORES['amarelo'], bg=CORES['fundo'])
        self.lbl_mesa_sel.pack(side='left', padx=5)
        
        self.btn_renomear = tk.Button(fr_topo_det, text="✏️ RENOMEAR", bg=CORES['busca'], fg='white', font=('Arial', 8, 'bold'), command=self.janela_renomear_mesa, state='disabled')
        self.btn_renomear.pack(side='right', padx=5)
        
        self.tree_mesa = ttk.Treeview(fr_det, columns=('id','Item','Qtd','Total'), show='headings', height=10)
        self.tree_mesa.heading('id', text='ID'); self.tree_mesa.column('id', width=40, anchor='center')
        self.tree_mesa.heading('Item', text='Produto'); self.tree_mesa.column('Item', width=180, anchor='w')
        self.tree_mesa.heading('Qtd', text='Qtd'); self.tree_mesa.column('Qtd', width=50, anchor='center')
        self.tree_mesa.heading('Total', text='R$'); self.tree_mesa.column('Total', width=80, anchor='center')
        self.tree_mesa.pack(fill='both', expand=True, pady=5)
        self.tree_mesa.bind("<Double-1>", self.ao_clicar_duplo_comanda)

        fr_add = tk.LabelFrame(fr_det, text=" Pesquisar e Lançar Produto ", bg=CORES['painel'], fg='white', font=('Arial', 9, 'bold'), pady=8, padx=5)
        fr_add.pack(fill='x', pady=5)
        fr_add.columnconfigure(0, weight=3)
        fr_add.columnconfigure(1, weight=1)
        fr_add.columnconfigure(2, weight=1)

        fr_busca_hibrida = tk.Frame(fr_add, bg=CORES['painel'])
        fr_busca_hibrida.grid(row=0, column=0, padx=5, sticky='ew')
        fr_busca_hibrida.columnconfigure(0, weight=1)

        self.ent_busca_prod = tk.Entry(fr_busca_hibrida, font=('Arial', 11), bg='white', fg='gray')
        self.ent_busca_prod.grid(row=0, column=0, sticky='ew')
        self.ent_busca_prod.insert(0, "Digite o nome ou código...")
        self.ent_busca_prod.bind("<FocusIn>", self.limpar_placeholder_busca)
        self.ent_busca_prod.bind("<FocusOut>", self.restaurar_placeholder_busca)
        self.ent_busca_prod.bind("<KeyRelease>", self.filtrar_produtos_busca)
        self.ent_busca_prod.bind("<Down>", lambda e: self.list_sugestoes.focus_set() if self.list_sugestoes.winfo_viewable() else None)
        
        self.btn_ver_todos = tk.Button(fr_busca_hibrida, text="🔽", font=('Arial', 8), bg='white', fg='black', bd=1, relief='flat', command=self.exibir_lista_completa)
        self.btn_ver_todos.grid(row=0, column=1, sticky='ns')
        
        self.ent_qtd_mesa = tk.Entry(fr_add, font=('Arial', 11), justify='center', width=5)
        self.ent_qtd_mesa.insert(0, "1")
        self.ent_qtd_mesa.grid(row=0, column=1, padx=5, sticky='ew')
        
        tk.Button(fr_add, text="➕ LANÇAR", bg=CORES['azul'], fg='white', font=('Arial', 9, 'bold'), command=self.add_item_mesa).grid(row=0, column=2, padx=5, sticky='ew')

        self.list_sugestoes = tk.Listbox(fr_add, font=('Arial', 9), height=5, bg='white', fg='black', selectbackground=CORES['azul'], selectforeground='white', activestyle='none')
        self.list_sugestoes.grid(row=1, column=0, columnspan=3, padx=5, pady=2, sticky='ew')
        self.list_sugestoes.bind("<<ListboxSelect>>", self.selecionar_produto_lista)
        self.list_sugestoes.bind("<Motion>", self.efeito_hover_listbox)
        self.list_sugestoes.bind("<Return>", self.selecionar_produto_lista)
        self.list_sugestoes.grid_remove()

        fr_checkout = tk.Frame(fr_det, bg=CORES['fundo'])
        fr_checkout.pack(fill='x', pady=10)
        self.lbl_total_mesa = tk.Label(fr_checkout, text="TOTAL: R$ 0.00", font=('Arial', 18, 'bold'), fg=CORES['verde'], bg=CORES['fundo'])
        self.lbl_total_mesa.pack(pady=5)
        
        self.cb_pag_mesa = ttk.Combobox(fr_checkout, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"], font=('Arial', 10), state="readonly")
        self.cb_pag_mesa.current(0); self.cb_pag_mesa.pack(pady=5, fill='x')
        tk.Button(fr_checkout, text="🔒 FECHAR MESA / ABRIR PAINEL DE DIVISÃO", bg=CORES['vermelho'], fg='white', font=('Arial', 11, 'bold'), command=self.fechar_mesa).pack(pady=5, fill='x', ipady=3)
        self.atualizar_cores_mesas()

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
        if index >= 0:
            self.list_sugestoes.selection_clear(0, tk.END); self.list_sugestoes.selection_set(index); self.list_sugestoes.activate(index)

    def exibir_lista_completa(self):
        if self.list_sugestoes.winfo_viewable(): self.list_sugestoes.grid_remove(); return
        self.limpar_placeholder_busca(None)
        self.list_sugestoes.delete(0, tk.END)
        if self.lista_produtos_cache:
            self.list_sugestoes.grid()
            for prod in self.lista_produtos_cache: self.list_sugestoes.insert(tk.END, prod['texto_completo'])

    def filtrar_produtos_busca(self, event):
        if event.keysym in ["Up", "Down", "Left", "Right", "Return"]: return
        termo = self.ent_busca_prod.get().strip().lower()
        if not termo or termo == "digite o nome ou código...": self.list_sugestoes.grid_remove(); self.produto_selecionado_id = None; return
        resultados = [p for p in self.lista_produtos_cache if termo in p['nome'].lower() or termo in str(p['id'])]
        self.list_sugestoes.delete(0, tk.END)
        if resultados:
            self.list_sugestoes.grid()
            for prod in resultados: self.list_sugestoes.insert(tk.END, prod['texto_completo'])
        else: self.list_sugestoes.grid_remove(); self.produto_selecionado_id = None

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
            self.list_sugestoes.grid_remove()
            self.ent_qtd_mesa.focus_set(); self.ent_qtd_mesa.selection_range(0, tk.END)
        except Exception as e: print(e)

    # --- NOVA TELA DE SELEÇÃO: VÍNCULO DO ESPETO DA JANTINHA ---
    def abrir_selecao_espeto_jantinha(self, qtd_jantinha):
        janela_esp = tk.Toplevel(self)
        janela_esp.title("Componentes da Jantinha")
        janela_esp.geometry("380x300")
        janela_esp.configure(bg=CORES['painel'])
        janela_esp.resizable(False, False)
        janela_esp.transient(self)
        
        tk.Label(janela_esp, text="🍢 SELECIONE O ESPETO DA JANTINHA", font=('Arial', 11, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=8)
        
        ent_busca = tk.Entry(janela_esp, font=('Arial', 11), width=25)
        ent_busca.insert(0, "ESPETO")
        ent_busca.pack(pady=4)
        
        list_esp = tk.Listbox(janela_esp, font=('Arial', 10), height=6, bg='white', fg='black', selectbackground=CORES['azul'])
        list_esp.pack(fill='both', expand=True, padx=15, pady=5)
        
        espeto_id_selecionado = [None] # Escopo local mutável

        def filtrar_espetos(event=None):
            termo = ent_busca.get().strip().lower()
            list_esp.delete(0, tk.END)
            for p in self.lista_produtos_cache:
                if "espeto" in p['nome'].lower() and (not termo or termo in p['nome'].lower()):
                    list_esp.insert(tk.END, p['texto_completo'])
        
        ent_busca.bind("<KeyRelease>", filtrar_espetos)
        filtrar_espetos()

        def confirmar_espeto():
            sel = list_esp.curselection()
            if not sel:
                messagebox.showwarning("Aviso", "Escolha qual espeto acompanha a jantinha!", parent=janela_esp)
                return
            texto = list_esp.get(sel[0])
            espeto_id_selecionado[0] = int(texto.split(' - ')[0])
            janela_esp.destroy()

        tk.Button(janela_esp, text="VINCULAR AO PEDIDO", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=confirmar_espeto).pack(pady=10)
        
        janela_esp.update()
        janela_esp.grab_set()
        self.wait_window(janela_esp)
        return espeto_id_selecionado[0]

    def selecionar_mesa(self, m):
        self.mesa_atual = m
        self.btn_renomear.config(state='normal')
        self.lbl_mesa_sel.config(text=f"{self.nomes_mesas[m]} - PAINEL")
        conn = sqlite3.connect(DB_NAME)
        atend = conn.cursor().execute("SELECT id FROM atendimentos WHERE mesa_id=? AND status='ABERTO'", (m,)).fetchone()
        conn.close()
        self.atendimento_id_actual = atend[0] if atend else None
        self.carregar_mesa()

    def janela_renomear_mesa(self):
        if not self.mesa_atual: return
        janela = tk.Toplevel(self); janela.title("Renomear"); janela.geometry("320x150"); janela.configure(bg=CORES['painel']); janela.resizable(False, False); janela.transient(self)
        tk.Label(janela, text=f"Identificador da Mesa {self.mesa_atual:02d}:", bg=CORES['painel'], fg='white').pack(pady=10)
        ent_nome = tk.Entry(janela, font=('Arial', 12), width=22, justify='center'); ent_nome.insert(0, self.nomes_mesas[self.mesa_atual]); ent_nome.pack(pady=5); ent_nome.focus_set(); ent_nome.selection_range(0, tk.END)
        def salvar_nome():
            novo_nome = ent_nome.get().strip().upper()
            if not novo_nome: novo_nome = f"MESA {self.mesa_atual:02d}"
            self.nomes_mesas[self.mesa_atual] = novo_nome
            self.btns_mesa[self.mesa_atual].config(text=novo_nome)
            self.lbl_mesa_sel.config(text=f"{novo_nome} - PAINEL"); janela.destroy()
        tk.Button(janela, text="SALVAR", bg=CORES['verde'], fg='white', command=salvar_nome).pack(pady=12)
        janela.update(); janela.grab_set()

    def carregar_mesa(self):
        self.tree_mesa.delete(*self.tree_mesa.get_children())
        total = 0
        if not self.atendimento_id_actual: self.lbl_total_mesa.config(text="TOTAL: R$ 0.00"); return
        conn = sqlite3.connect(DB_NAME)
        itens = conn.cursor().execute("SELECT id, produto_nome, qtd, total FROM itens_atendimento WHERE atendimento_id=?", (self.atendimento_id_actual,)).fetchall()
        conn.close()
        for i in itens: self.tree_mesa.insert('','end',values=i); total += i[3]
        self.lbl_total_mesa.config(text=f"TOTAL: R$ {total:.2f}")

    def atualizar_cores_mesas(self):
        conn = sqlite3.connect(DB_NAME)
        ocupadas = [x[0] for x in conn.cursor().execute("SELECT DISTINCT mesa_id FROM atendimentos WHERE status='ABERTO'").fetchall()]
        conn.close()
        for i in range(1, 21): self.btns_mesa[i].config(text=self.nomes_mesas[i], bg=CORES['vermelho'] if i in ocupadas else CORES['verde'])

    def add_item_mesa(self):
        if not self.mesa_atual: messagebox.showwarning("!","Selecione uma mesa"); return
        if not self.produto_selecionado_id: messagebox.showwarning("Aviso", "Selecione um produto."); return
            
        try:
            qtd = int(self.ent_qtd_mesa.get())
            pid = self.produto_selecionado_id
            
            conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
            res = cursor.execute("SELECT nome, preco, estoque, codigo FROM produtos WHERE id=?",(pid,)).fetchone()
            if not res: messagebox.showerror("Erro", "Produto sumiu."); conn.close(); return
            nome_prod, preco_prod, estoque_prod, codigo_prod = res
            
            if estoque_prod < qtd: messagebox.showerror("Erro", f"Sem estoque de {nome_prod}!"); conn.close(); return
            
            espeto_vinculado_id = None
            # GATILHO: Se for uma Jantinha, abre a tela de busca semi-pronta de espetos
            if "jantinha" in nome_prod.lower():
                espeto_vinculado_id = self.abrir_selecao_espeto_jantinha(qtd)
                if not espeto_vinculado_id:
                    conn.close(); return
                
                esp_res = cursor.execute("SELECT nome, estoque FROM produtos WHERE id=?", (espeto_vinculado_id,)).fetchone()
                if esp_res[1] < qtd:
                    messagebox.showerror("Erro", f"Falta estoque do espeto escolhido ({esp_res[0]})!"); conn.close(); return
                
                # Desconta o espeto específico escolhido pelo operador
                cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (qtd, espeto_vinculado_id))
                nome_prod = f"{nome_prod} (+ {esp_res[0]})"

            total = preco_prod * qtd
            if not self.atendimento_id_actual:
                dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO atendimentos (mesa_id, data_abertura, status) VALUES (?,?,?)", (self.mesa_atual, dt_agora, 'ABERTO'))
                self.atendimento_id_actual = cursor.lastrowid

            cursor.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (self.atendimento_id_actual, nome_prod, qtd, total))
            cursor.execute("UPDATE produtos SET estoque=estoque-? WHERE id=?",(qtd,pid))
            
            conn.commit(); conn.close()
            
            self.ent_busca_prod.delete(0, tk.END); self.ent_busca_prod.insert(0, "Digite o nome ou código..."); self.ent_busca_prod.config(fg='gray')
            self.ent_qtd_mesa.delete(0, tk.END); self.ent_qtd_mesa.insert(0, "1"); self.produto_selecionado_id = None
            self.carregar_mesa(); self.app.atualizar_todos_produtos(); self.atualizar_cores_mesas()
        except Exception as e: print(e)

    def fechar_mesa(self):
        if not self.atendimento_id_actual or not self.tree_mesa.get_children(): return
        conn = sqlite3.connect(DB_NAME)
        total_atual = conn.cursor().execute("SELECT SUM(total) FROM itens_atendimento WHERE atendimento_id=?", (self.atendimento_id_actual,)).fetchone()[0]
        conn.close()
        self.abrir_janela_desconto(total_atual if total_atual else 0.0)

    def abrir_janela_desconto(self, total_original):
        janela_desc = tk.Toplevel(self); janela_desc.title(f"Fechamento - Mesa {self.mesa_atual:02d}"); janela_desc.geometry("420x380"); janela_desc.configure(bg=CORES['painel']); janela_desc.resizable(False, False); janela_desc.transient(self)
        self.saldo_restante = total_original
        id_comanda_fechada = self.atendimento_id_actual; numero_mesa_fechada = self.mesa_atual

        # DENTRO DE abrir_janela_desconto na aba_mesas.py:
        def emitir_recibo_comanda():
            from tkinter import filedialog # Importação local ou no topo do arquivo
            import os
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from sistema.config import DADOS_EMPRESA
            
            # Pergunta onde salvar o PDF
            nome_pdf = filedialog.asksaveasfilename(
                initialfile=f"Recibo_Comanda_{id_comanda_fechada}.pdf",
                defaultextension=".pdf",
                filetypes=[("Documentos PDF", "*.pdf")],
                title="Escolha onde salvar o Recibo"
            )
            if not nome_pdf: # Se o usuário cancelar
                return
                
            try:
                dados_tabela = [["PRODUTO", "QTD", "TOTAL"]]; pagamentos_registrados = []; descontos_e_ajustes = 0
                conn = sqlite3.connect(DB_NAME)
                dados_pai = conn.cursor().execute("SELECT data_abertura, data_fechamento, desconto, pagamento FROM atendimentos WHERE id=?", (id_comanda_fechada,)).fetchone()
                itens_fechados = conn.cursor().execute("SELECT produto_nome, qtd, total FROM itens_atendimento WHERE atendimento_id=?", (id_comanda_fechada,)).fetchall()
                conn.close()
                
                # Gera o documento no caminho escolhido
                doc = SimpleDocTemplate(nome_pdf, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30); story = []
                styles = getSampleStyleSheet()
                style_titulo = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#2c3e50'))
                style_empresa = ParagraphStyle('E1', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, textColor=colors.HexColor('#7f8c8d'))
                style_normal = ParagraphStyle('N1', parent=styles['Normal'], fontSize=10, leading=14)
                style_negrito = ParagraphStyle('B1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14)
                story.append(Paragraph(f"<b>{DADOS_EMPRESA['nome']}</b>", style_titulo)); story.append(Spacer(1, 4))
                story.append(Paragraph(f"CNPJ: {DADOS_EMPRESA['cnpj']} | Tel: {DADOS_EMPRESA['telefone']}", style_empresa))
                story.append(Paragraph(f"Endereço: {DADOS_EMPRESA['endereco']}", style_empresa)); story.append(Spacer(1, 10))
                story.append(Paragraph("<b>RECIBO DE CONSUMO INDIVIDUAL</b>", ParagraphStyle('Sub', parent=style_titulo, fontSize=12)))
                story.append(Paragraph(f"<b>IDENTIFICAÇÃO: {self.nomes_mesas[numero_mesa_fechada]} | COMANDA Nº: {id_comanda_fechada}</b>", style_negrito))
                story.append(Paragraph(f"Abertura: {dados_pai[0]} | Encerramento: {dados_pai[1]}", style_normal)); story.append(Spacer(1, 10))
                for item in itens_fechados:
                    nome, qtd, total = item
                    if "PAG. PARCIAL" in nome: pagamentos_registrados.append((dados_pai[3], total))
                    elif "ABATIMENTO" in nome or "DESCONTO" in nome: descontos_e_ajustes += total; dados_tabela.append([nome, str(qtd), f"R$ {total:.2f}"])
                    else: dados_tabela.append([nome, str(qtd), f"R$ {total:.2f}"])
                tabela_itens = Table(dados_tabela, colWidths=[300, 60, 100])
                tabela_itens.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')), ('TOPPADDING', (0, 1), (-1, -1), 4), ('BOTTOMPADDING', (0, 1), (-1, -1), 4)]))
                story.append(tabela_itens); story.append(Spacer(1, 15))
                story.append(Paragraph(f"<b>SUBTOTAL CONSUMO:</b> R$ {total_original:.2f}", style_normal))
                if dados_pai[2] > 0: story.append(Paragraph(f"<b>DESCONTO CONCEDIDO:</b> R$ {dados_pai[2]:.2f}", style_normal))
                story.append(Paragraph(f"<b>TOTAL LÍQUIDO PAGO:</b> R$ {total_original - dados_pai[2]:.2f}", style_negrito)); story.append(Spacer(1, 10))
                story.append(Paragraph(f"<b>FORMA DE LIQUIDAÇÃO:</b> {dados_pai[3]}", style_normal)); story.append(Spacer(1, 25))
                story.append(Paragraph("Agradecemos a preferência! Volte Sempre.", ParagraphStyle('R1', parent=style_empresa, fontName='Helvetica-Oblique', fontSize=11)))
                doc.build(story)
                if hasattr(os, 'startfile'): os.startfile(nome_pdf)
                else: os.system(f'xdg-open "{nome_pdf}"')
            except Exception as e: messagebox.showerror("Erro PDF", f"Falha ao gerar recibo: {e}")

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

        def salvar_pagamento_parcial_banco(valor_pago, forma_pgto):
            conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
            cursor.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_comanda_fechada, f"ABATIMENTO RÁPIDO ({forma_pgto})", 1, -valor_pago))
            conn.commit(); conn.close()
            self.saldo_restante -= valor_pago
            lbl_saldo.config(text=f"SALDO RESTANTE: R$ {self.saldo_restante:.2f}", fg=CORES['vermelho'] if self.saldo_restante > 0 else CORES['verde'])
            self.carregar_mesa(); self.app.aba_caixa.carregar_historico()
            if self.saldo_restante <= 0.01: finalizar_mesa_totalmente(deve_perguntar=False)
            else: ent_valor_pagar.delete(0, tk.END); ent_valor_pagar.insert(0, f"{self.saldo_restante:.2f}"); messagebox.showinfo("Sucesso", f"Recebido R$ {valor_pago:.2f}!", parent=janela_desc)

        def receber_pagamento_parcial():
            try:
                valor_pago = float(ent_valor_pagar.get().replace(',', '.'))
                if valor_pago <= 0 or valor_pago > self.saldo_restante + 0.01: raise ValueError
            except ValueError: messagebox.showerror("Erro", "Valor inserido inválido.", parent=janela_desc); return
            forma_pgto = cb_forma_parcial.get()
            if forma_pgto == "DINHEIRO": solicitar_troco_dinheiro(valor_pago, lambda: salvar_pagamento_parcial_banco(valor_pago, forma_pgto))
            else:
                if messagebox.askyesno("Confirmar", f"Receber R$ {valor_pago:.2f} no {forma_pgto}?", parent=janela_desc): salvar_pagamento_parcial_banco(valor_pago, forma_pgto)

        def fechar_mesa_final_banco(desconto, forma_pgto_final):
            conn = sqlite3.connect(DB_NAME); cursor = conn.cursor(); dt_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if desconto > 0: 
                cursor.execute("INSERT INTO itens_atendimento (atendimento_id, produto_nome, qtd, total) VALUES (?,?,?,?)", (id_comanda_fechada, "DESCONTO MANUAL", 1, -desconto))
            
            # Atualiza o encerramento do registro Pai
            cursor.execute("UPDATE atendimentos SET data_fechamento=?, desconto=?, pagamento=?, status='FECHADO' WHERE id=?", (dt_agora, desconto, forma_pgto_final, id_comanda_fechada))
            
            # --- CORREÇÃO CIRÚRGICA DE DISCRIMINAÇÃO E MULTI-PAGAMENTOS ---
            itens_venda = cursor.execute("SELECT produto_nome, qtd, total FROM itens_atendimento WHERE atendimento_id=?", (id_comanda_fechada,)).fetchall()
            hora_fechamento = dt_agora.split(' ')[1]
            origem_txt = f"Mesa {numero_mesa_fechada:02d}"
            
            for item in itens_venda:
                nome_item = item[0]
                total_item = item[2]
                
                # Se for uma linha de abatimento de conta dividida, preserva a forma de pagamento real dela!
                if "ABATIMENTO RÁPIDO" in nome_item:
                    # Extrai o texto de dentro dos parenteses, ex: "ABATIMENTO RÁPIDO (DINHEIRO)" -> "DINHEIRO"
                    forma_real_parcial = nome_item.split('(')[1].split(')')[0]
                    cursor.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_fechamento, origem_txt, f"PAG. PARCIAL ({forma_real_parcial})", item[1], total_item, forma_real_parcial)
                    )
                elif "DESCONTO" in nome_item:
                    cursor.execute(
                        "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                        (hora_fechamento, origem_txt, nome_item, item[1], total_item, forma_pgto_final)
                    )
                else:
                    # Produtos normais entram vinculados à forma de pagamento que liquidou o restante da conta
                    if total_item != 0:
                        cursor.execute(
                            "INSERT INTO vendas_consolidadas (hora, origem, produto, qtd, total, pagamento) VALUES (?,?,?,?,?,?)",
                            (hora_fechamento, origem_txt, nome_item, item[1], total_item, forma_pgto_final)
                        )
            
            conn.commit(); conn.close()
            self.nomes_mesas[numero_mesa_fechada] = f"MESA {numero_mesa_fechada:02d}"
            self.atendimento_id_actual = None; self.carregar_mesa(); self.atualizar_cores_mesas(); self.app.aba_caixa.carregar_historico()
            if messagebox.askyesno("Mesa Encerrada", "Mesa fechada!\nDeseja emitir o recibo em PDF?"): emitir_recibo_comanda()
            janela_desc.destroy()

        def finalizar_mesa_totalmente(deve_perguntar=True):
            try:
                desconto = float(ent_desc.get().replace(',', '.'))
                if desconto < 0 or desconto > self.saldo_restante: raise ValueError
            except ValueError: messagebox.showerror("Erro", "Valor de desconto inválido.", parent=janela_desc); return
            total_final = self.saldo_restante - desconto; forma_pgto_final = self.cb_pag_mesa.get()
            if forma_pgto_final == "DINHEIRO": solicitar_troco_dinheiro(total_final, lambda: fechar_mesa_final_banco(desconto, forma_pgto_final))
            else:
                texto_confirma = f"Total Restante: R$ {self.saldo_restante:.2f}\nDesconto: R$ {desconto:.2f}\nValor Final: R$ {total_final:.2f}\nFechar com {forma_pgto_final}?"
                if not deve_perguntar or messagebox.askyesno("Confirmar", texto_confirma, parent=janela_desc): fechar_mesa_final_banco(desconto, forma_pgto_final)

        tk.Label(janela_desc, text=f"FECHAMENTO DA MESA {self.mesa_atual:02d}", font=('Arial', 13, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        lbl_saldo = tk.Label(janela_desc, text=f"SALDO RESTANTE: R$ {total_original:.2f}", font=('Arial', 14, 'bold'), bg=CORES['painel'], fg=CORES['verde']); lbl_saldo.pack(pady=5)
        fr_divisao = tk.LabelFrame(janela_desc, text=" Receber Pagamento Parcial (Dividir Conta) ", bg=CORES['painel'], fg='white', font=('Arial', 10, 'bold'), padx=10, pady=10); fr_divisao.pack(fill='x', padx=15, pady=5)
        tk.Label(fr_divisao, text="Valor a pagar agora (R$):", bg=CORES['painel'], fg='white').grid(row=0, column=0, sticky='w', pady=2)
        ent_valor_pagar = tk.Entry(fr_divisao, font=('Arial', 11), width=14, justify='center'); ent_valor_pagar.insert(0, f"{total_original:.2f}"); ent_valor_pagar.grid(row=0, column=1, pady=2, padx=5)
        tk.Label(fr_divisao, text="Forma de Pagamento:", bg=CORES['painel'], fg='white').grid(row=1, column=0, sticky='w', pady=2)
        cb_forma_parcial = ttk.Combobox(fr_divisao, values=["DINHEIRO", "PIX", "CRÉDITO", "DÉBITO"], width=12, state="readonly"); cb_forma_parcial.current(0); cb_forma_parcial.grid(row=1, column=1, pady=2, padx=5)
        tk.Button(fr_divisao, text="RECEBER PARTE", bg=CORES['azul'], fg='white', font=('Arial', 9, 'bold'), command=receber_pagamento_parcial).grid(row=0, column=2, rowspan=2, padx=10, ipady=4)
        fr_total = tk.LabelFrame(janela_desc, text=" Encerrar Saldo Restante / Aplicar Desconto ", bg=CORES['painel'], fg='white', font=('Arial', 10, 'bold'), padx=10, pady=10); fr_total.pack(fill='x', padx=15, pady=10)
        tk.Label(fr_total, text="Conceder Desconto (R$):", bg=CORES['painel'], fg='white').pack(side='left', padx=5)
        ent_desc = tk.Entry(fr_total, font=('Arial', 11), width=12, justify='center'); ent_desc.insert(0, "0.00"); ent_desc.pack(side='left', padx=5)
        tk.Button(fr_total, text="FECHAR CONTA", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), command=lambda: finalizar_mesa_totalmente(deve_perguntar=True)).pack(side='right', padx=5, ipady=2)
        janela_desc.update(); janela_desc.grab_set(); ent_valor_pagar.focus_set(); ent_valor_pagar.selection_range(0, tk.END)

    def ao_clicar_duplo_comanda(self, event):
        sel = self.tree_mesa.selection()
        if not sel: return
        item_valores = self.tree_mesa.item(sel[0])['values']
        self.abrir_janela_editar_qtd(item_valores[0], item_valores[1], item_valores[2])

    def abrir_janela_editar_qtd(self, item_venda_id, produto_nome, qtd_atual):
        janela_qtd = tk.Toplevel(self); janela_qtd.title("Editar"); janela_qtd.geometry("380x220"); janela_qtd.configure(bg=CORES['painel']); janela_qtd.resizable(False, False); janela_qtd.transient(self)
        tk.Label(janela_qtd, text="EDITAR OU REVERTER ITEM", font=('Arial', 12, 'bold'), bg=CORES['painel'], fg=CORES['amarelo']).pack(pady=5)
        tk.Label(janela_qtd, text=f"{produto_nome}", font=('Arial', 11), bg=CORES['painel'], fg='white', wraplength=340).pack(pady=2)
        tk.Label(janela_qtd, text="Nova Quantidade:", bg=CORES['painel'], fg='white').pack(pady=5)
        ent_nova_qtd = tk.Entry(janela_qtd, font=('Arial', 12), width=10, justify='center'); ent_nova_qtd.insert(0, str(qtd_atual)); ent_nova_qtd.pack(pady=2)
        fr_botoes_popup = tk.Frame(janela_qtd, bg=CORES['painel']); fr_botoes_popup.pack(pady=15)
        def salvar_nova_quantidade():
            try:
                nova_qtd = int(ent_nova_qtd.get())
                if nova_qtd <= 0: raise ValueError
            except ValueError: messagebox.showerror("Erro", "Quantidade inválida.", parent=janela_qtd); return
            if nova_qtd == qtd_atual: janela_qtd.destroy(); return
            conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
            prod_info = cursor.execute("SELECT id, preco, estoque, codigo FROM produtos WHERE nome=?", (produto_nome.split(' (+ ')[0],)).fetchone()
            if not prod_info: messagebox.showerror("Erro", "Não localizado.", parent=janela_qtd); conn.close(); return
            prod_id, preco_unitario, estoque_atual, codigo_prod = prod_info; diferenca_qtd = nova_qtd - qtd_atual 
            if diferenca_qtd > estoque_atual: messagebox.showerror("Erro", f"Sem estoque!\nDisponível: {estoque_atual}", parent=janela_qtd); conn.close(); return
            novo_total_venda = preco_unitario * nova_qtd
            cursor.execute("UPDATE itens_atendimento SET qtd=?, total=? WHERE id=?", (nova_qtd, novo_total_venda, item_venda_id))
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (diferenca_qtd, prod_id))
            conn.commit(); conn.close(); janela_qtd.destroy(); self.carregar_mesa(); self.app.atualizar_todos_produtos()
        def remover_produto_completamente():
            if messagebox.askyesno("Confirmar Exclusão", f"Deseja remover?", parent=janela_qtd):
                conn = sqlite3.connect(DB_NAME); cursor = conn.cursor()
                prod_info = cursor.execute("SELECT id, codigo FROM produtos WHERE nome=?", (produto_nome.split(' (+ ')[0],)).fetchone()
                if prod_info: cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE id=?", (qtd_atual, prod_info[0]))
                cursor.execute("DELETE FROM itens_atendimento WHERE id=?", (item_venda_id,))
                conn.commit(); conn.close(); janela_qtd.destroy(); self.carregar_mesa(); self.app.atualizar_todos_produtos(); messagebox.showinfo("Sucesso", "Removido!")
        tk.Button(fr_botoes_popup, text="SALVAR", bg=CORES['verde'], fg='white', font=('Arial', 10, 'bold'), width=14, command=salvar_nova_quantidade).pack(side='left', padx=10)
        tk.Button(fr_botoes_popup, text="EXCLUIR ITEM", bg=CORES['vermelho'], fg='white', font=('Arial', 10, 'bold'), width=14, command=remover_produto_completamente).pack(side='left', padx=10)
        janela_qtd.update(); janela_qtd.grab_set(); ent_nova_qtd.focus_set(); ent_nova_qtd.selection_range(0, tk.END)