# 🔒 GUIA DE BRANCH PROTECTION - MASTER

## Passo a Passo Completo

### 1️⃣ Acessar Configurações do Repositório

1. Vá para: https://github.com/JulianoSaroba123/jsp_erp
2. Clique em **Settings** (último item do menu superior)
3. No menu lateral esquerdo, clique em **Branches**

---

### 2️⃣ Criar Nova Regra de Proteção

1. Clique no botão **Add branch protection rule** (ou **Add rule**)
2. No campo **Branch name pattern**, digite: `master`

---

### 3️⃣ Configurar Proteções Obrigatórias

#### ✅ **Require a pull request before merging**
- [x] Marque esta opção
- **Resultado:** Ninguém pode fazer push direto para master, apenas via PR

**Configurações internas (expandir):**
- [x] **Require approvals:** 1 approval (opcional para projetos solo)
- [ ] **Dismiss stale pull request approvals when new commits are pushed** (opcional)
- [x] **Require review from Code Owners** (deixe desmarcado se não tem CODEOWNERS)

---

#### ✅ **Require status checks to pass before merging**
- [x] Marque esta opção
- **Resultado:** CI deve estar verde antes do merge

**Sub-configurações:**
1. [x] Marque **Require branches to be up to date before merging**
   - **Importante:** Força rebase/merge de master antes do PR ser aceito
   
2. Na caixa de busca **Search for status checks**, digite: `pytest`
   - Aguarde carregar os checks disponíveis
   - Selecione: `pytest` (job do workflow tests.yml)
   - **Se não aparecer:** Primeiro crie um PR de teste, depois volte aqui

---

#### ✅ **Require conversation resolution before merging** (Opcional)
- [ ] Marque se quiser forçar resolução de todos os comentários
- **Recomendado:** Deixar desmarcado para projetos solo

---

#### ✅ **Require signed commits** (Opcional - Avançado)
- [ ] Deixe desmarcado (requer configuração GPG)

---

#### ✅ **Require linear history** (Recomendado)
- [x] Marque esta opção
- **Resultado:** Força squash ou rebase, evita merge commits feios
- **Benefício:** Histórico git limpo e linear

---

#### ✅ **Include administrators** (Decisão importante)
- [ ] **NÃO marque** se você quer poder fazer push direto em emergências
- [x] **MARQUE** se quer disciplina total (mesmo você precisa de PR)

**Recomendação para JSP:** Deixar desmarcado enquanto você é o único dev

---

#### ✅ **Allow force pushes** (CRÍTICO)
- [ ] **SEMPRE desmarcado**
- **Motivo:** Force push em master destrói histórico

---

#### ✅ **Allow deletions** (CRÍTICO)
- [ ] **SEMPRE desmarcado**
- **Motivo:** Ninguém deve deletar master

---

### 4️⃣ Salvar Regra

1. Scroll até o final da página
2. Clique em **Create** (ou **Save changes**)
3. Aguarde confirmação: "Branch protection rule created"

---

## ✅ Validação

Após salvar, tente fazer push direto para master:

```bash
git checkout master
echo "teste" >> test.txt
git add test.txt
git commit -m "test: direct push"
git push
```

**Resultado esperado:**
```
remote: error: GH006: Protected branch update failed for refs/heads/master.
remote: error: Changes must be made through a pull request.
```

✅ **Se ver esse erro:** Proteção está funcionando!

---

## 🔧 Fluxo de Trabalho Correto Após Branch Protection

### Novo desenvolvimento:

```bash
# 1. Criar branch de feature
git checkout -b feature/nova-funcionalidade

# 2. Fazer alterações e commitar
git add .
git commit -m "feat: implementar nova funcionalidade"

# 3. Enviar para repositório
git push origin feature/nova-funcionalidade

# 4. Criar Pull Request no GitHub
#    - Base: master
#    - Compare: feature/nova-funcionalidade

# 5. Aguardar CI passar (tests deve estar verde)

# 6. Fazer merge pelo GitHub
#    - Opção recomendada: "Squash and merge"
```

---

## 📋 Checklist de Verificação

Após configurar, confirme:

- [ ] Tentou push direto em master e foi bloqueado
- [ ] CI aparece como required check no PR
- [ ] Badge no README está verde
- [ ] Conseguiu criar PR normalmente
- [ ] Conseguiu fazer merge após CI passar

---

## 🆘 Troubleshooting

### Problema: "Status check pytest não aparece na busca"

**Solução:**
1. Crie um PR de teste qualquer
2. Aguarde o workflow rodar
3. Volte em Settings → Branches → Edit rule
4. Agora o check `pytest` deve aparecer

### Problema: "Preciso fazer hotfix urgente em master"

**Solução temporária:**
1. Settings → Branches → Edit rule (master)
2. Desmarque temporariamente as proteções
3. Faça o push
4. **IMPORTANTE:** Reative as proteções imediatamente

**Solução definitiva:**
1. Configure "Include administrators" como desmarcado
2. Você sempre pode fazer push direto quando necessário
3. Mas não abuse - use PRs sempre que possível

---

## 📊 Status Atual Recomendado

```
Branch name pattern: master
✅ Require pull request (1 approval)
✅ Require status checks (pytest)
✅ Require branches to be up to date
✅ Require linear history
❌ Include administrators (para flexibilidade)
❌ Allow force pushes (proteção)
❌ Allow deletions (proteção)
```

**Salve este documento para referência futura!**
