# 🔍 Sistema de Busca Automática Profissional

## Visão Geral

Sistema ERP enterprise com automação inteligente de cadastros via APIs externas:
- **BrasilAPI**: Consulta de dados empresariais (CNPJ)
- **ViaCEP**: Consulta de endereços (CEP)

## ✨ Funcionalidades

### 🏢 Busca Automática por CNPJ
- ✅ **Validação real** com dígitos verificadores (não apenas contagem)
- ✅ **Debounce inteligente** de 600ms (otimizado para digitação)
- ✅ **Cancelamento automático** de requisições pendentes (AbortController)
- ✅ **Feedback visual** com spinner + mensagens de sucesso/erro
- ✅ **Preenchimento automático** de 13+ campos:
  - Nome (Razão Social)
  - Razão Social (Trade Name) 
  - Email
  - Telefone Principal
  - Telefone Alternativo
  - CEP
  - Logradouro
  - Número
  - Complemento
  - Bairro
  - Cidade
  - Estado

### 📮 Busca Automática por CEP
- ✅ **Validação** de 8 dígitos
- ✅ **Debounce otimizado** de 500ms (mais rápido que CNPJ)
- ✅ **Cancelamento automático** de requisições pendentes
- ✅ **Feedback profissional** (spinner + mensagens)
- ✅ **Preenchimento inteligente** de endereço completo:
  - Logradouro
  - Bairro
  - Cidade
  - Estado

## 🎯 Arquitetura Técnica

### Componentes Principais

```typescript
// Estados de Loading
const [isFetchingCnpj, setIsFetchingCnpj] = useState(false);
const [isFetchingCep, setIsFetchingCep] = useState(false);

// Estados de Feedback
const [cnpjSuccess, setCnpjSuccess] = useState<string | null>(null);
const [cnpjError, setCnpjError] = useState<string | null>(null);
const [cepSuccess, setCepSuccess] = useState<string | null>(null);
const [cepError, setCepError] = useState<string | null>(null);

// Refs para Cancelamento
const cnpjAbortRef = useRef<AbortController | null>(null);
const cepAbortRef = useRef<AbortController | null>(null);
```

### Fluxo de Execução - CNPJ

```
1. Usuário digita CNPJ
   ↓
2. onChange remove formatação → só dígitos
   ↓
3. useEffect detecta mudança
   ↓
4. Validações iniciais:
   - É Pessoa Jurídica? ✓
   - Tem 14 dígitos? ✓
   - Dígitos verificadores válidos? ✓ (isValidCNPJ)
   ↓
5. Cancela requisição anterior (se existir)
   ↓
6. Inicia debounce de 600ms
   ↓
7. Executa fetchCnpjData:
   - Cria novo AbortController
   - Mostra spinner
   - Chama BrasilAPI
   - Preenche 13+ campos
   - Exibe mensagem de sucesso
   - Agenda busca de CEP (se retornou CEP)
   ↓
8. Limpa mensagem após 5 segundos
```

### Fluxo de Execução - CEP

```
1. Usuário digita CEP (ou vem do CNPJ)
   ↓
2. onChange remove formatação
   ↓
3. useEffect detecta mudança
   ↓
4. Validações: 8 dígitos? ✓
   ↓
5. Cancela requisição anterior (se existir)
   ↓
6. Inicia debounce de 500ms
   ↓
7. Executa fetchCepData:
   - Cria novo AbortController
   - Mostra spinner
   - Chama ViaCEP
   - Preenche logradouro/bairro/cidade/estado
   - Exibe mensagem de sucesso
   ↓
8. Limpa mensagem após 4 segundos
```

## 🛠️ Tratamento de Erros

### CNPJ
- **CNPJ inválido**: Validação local (dígitos verificadores)
- **404**: "CNPJ não encontrado na Receita Federal"
- **Timeout**: "Tempo esgotado. Tente novamente"
- **Genérico**: "Erro ao consultar CNPJ. Verifique sua conexão"

### CEP
- **CEP inválido**: Validação local (8 dígitos)
- **404**: "CEP não encontrado"
- **Timeout**: "Tempo esgotado. Tente novamente"
- **Genérico**: "Erro ao consultar CEP. Verifique sua conexão"

## 🎨 UX/UI

### Estados Visuais

| Estado | Indicador | Cor |
|--------|-----------|-----|
| Loading | Spinner animado | Azul |
| Sucesso | ✓ Mensagem com detalhes | Verde |
| Erro | ✗ Mensagem específica | Vermelho |
| Validação | Mensagem do formulário | Vermelho |

### Mensagens de Sucesso

**CNPJ:**
```
✓ Dados carregados: EMPRESA EXEMPLO LTDA (11 campos preenchidos)
```

**CEP:**
```
✓ Endereço carregado: Av Paulista, Bela Vista - São Paulo/SP
```

## 🚀 Performance

### Otimizações Implementadas

1. **Debounce Inteligente**: Evita requisições desnecessárias durante digitação
2. **AbortController**: Cancela requisições obsoletas (race conditions)
3. **Validação Local First**: Verifica dígitos antes de chamar API
4. **Cache Natural**: APIs externas fazem cache (BrasilAPI/ViaCEP)
5. **shouldDirty: true**: Marca formulário como editado (UX)
6. **shouldValidate: false**: Não valida durante preenchimento automático (performance)
7. **Limpeza Automática**: Remove mensagens de sucesso após timeout

### Métricas

- **Debounce CNPJ**: 600ms (otimizado para 14 dígitos)
- **Debounce CEP**: 500ms (otimizado para 8 dígitos)
- **Timeout BrasilAPI**: 10000ms (10 segundos)
- **Timeout ViaCEP**: 8000ms (8 segundos)
- **Sucesso CNPJ**: Auto-remove em 5s
- **Sucesso CEP**: Auto-remove em 4s

## 🔐 Segurança

### Validações

```typescript
// CNPJ: Validação completa dos dígitos verificadores
isValidCNPJ(cpfCnpj) // Valida algoritmo da Receita Federal

// CEP: Validação de formato
isValidCep(cep) // Verifica se tem exatamente 8 dígitos
```

### Cancelamento de Requisições

```typescript
// Evita race conditions e memory leaks
if (cnpjAbortRef.current) {
  cnpjAbortRef.current.abort();
}
```

## 📚 APIs Utilizadas

### BrasilAPI - CNPJ
- **URL**: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`
- **Método**: GET
- **Timeout**: 10s
- **Rate Limit**: Controlado pela API (uso responsável)
- **Documentação**: https://brasilapi.com.br/docs

### ViaCEP
- **URL**: `https://viacep.com.br/ws/{cep}/json/`
- **Método**: GET
- **Timeout**: 8s
- **Rate Limit**: Ilimitado (uso responsável)
- **Documentação**: https://viacep.com.br/

## 🧪 Casos de Teste

### Cenário 1: CNPJ Válido
```
Input: 06.990.590/0001-23 (Google Brasil)
Expected: 
- ✓ Razão Social: GOOGLE BRASIL INTERNET LTDA
- ✓ Email preenchido
- ✓ Telefones preenchidos
- ✓ Endereço completo
- Mensagem: "✓ Dados carregados: GOOGLE BRASIL... (11 campos)"
```

### Cenário 2: CNPJ Inválido
```
Input: 12.345.678/0001-00
Expected:
- ✗ Mensagem: "CNPJ inválido"
- Não faz requisição à API
```

### Cenário 3: CEP Válido
```
Input: 01310-100 (Av Paulista)
Expected:
- ✓ Logradouro: Avenida Paulista
- ✓ Bairro: Bela Vista
- ✓ Cidade: São Paulo
- ✓ Estado: SP
- Mensagem: "✓ Endereço carregado: Avenida Paulista, Bela Vista..."
```

### Cenário 4: Digitação Rápida
```
Input: Usuário digita "41.280.764/0001-65" rapidamente
Expected:
- Debounce aguarda 600ms após última tecla
- Apenas 1 requisição é feita
- Requisições intermediárias canceladas
```

## 🔄 Integração com React Hook Form

### Controlled Inputs

```typescript
// Campo CPF/CNPJ
value={maskCnpjCpf(cpfCnpj || '')}  // Display formatado
onChange={(e) => {
  const cleaned = onlyDigits(e.target.value);  // Armazena só dígitos
  setValue('cpf_cnpj', cleaned, { 
    shouldValidate: true,  // Valida imediatamente
    shouldDirty: true      // Marca como editado
  });
}}
```

### Watch para Auto-Trigger

```typescript
const cpfCnpj = watch('cpf_cnpj');  // React-ivo
const personType = watch('person_type');
const cep = watch('cep');

// useEffect dispara automaticamente quando mudam
useEffect(() => {
  // Lógica de busca...
}, [cpfCnpj, personType]);
```

## 📖 Referências

- [React Hook Form](https://react-hook-form.com/)
- [AbortController MDN](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [BrasilAPI Docs](https://brasilapi.com.br/docs)
- [ViaCEP Docs](https://viacep.com.br/)
- [Debounce Pattern](https://www.freecodecamp.org/news/javascript-debounce-example/)

## 👨‍💻 Manutenção

### Para Adicionar Nova API

1. Adicionar função em `api/external.ts`:
```typescript
export async function getNewData(param: string): Promise<NewDataType> {
  const response = await axios.get(`https://api.com/${param}`);
  return response.data;
}
```

2. Adicionar estado no componente:
```typescript
const [isFetchingNew, setIsFetchingNew] = useState(false);
const [newError, setNewError] = useState<string | null>(null);
const [newSuccess, setNewSuccess] = useState<string | null>(null);
const newAbortRef = useRef<AbortController | null>(null);
```

3. Adicionar useEffect com debounce + validação
4. Adicionar fetchNewData com AbortController
5. Atualizar UI com feedback visual

### Para Ajustar Debounce

```typescript
// Aumentar para digitação mais lenta
const timer = setTimeout(async () => {
  await fetchCnpjData(digits);
}, 1000); // Era 600ms

// Diminuir para resposta mais rápida
const timer = setTimeout(async () => {
  await fetchCepData(digits);
}, 300); // Era 500ms
```

---

**Desenvolvido por**: Engenharia de Sistemas JSP ERP
**Versão**: 2.0 (Profissional Enterprise)
**Data**: Abril 2026
