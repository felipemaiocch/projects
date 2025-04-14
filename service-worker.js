// Versão do cache
const CACHE_NAME = 'minigestor-v1';

// Arquivos para serem cacheados
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/assets/index.css',
  '/assets/index.js',
];

// Instalação do service worker e armazenamento em cache dos assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache aberto');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Limpar caches antigos quando uma nova versão do service worker é ativada
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estratégia de cache: Cache First, falling back to network
self.addEventListener('fetch', event => {
  // Ignorar requisições para Firebase e análises
  if (event.request.url.includes('firebaseio.com') || 
      event.request.url.includes('googleapis.com') ||
      event.request.url.includes('analytics')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - retornar a resposta do cache
        if (response) {
          return response;
        }
        
        // Clone da requisição
        const fetchRequest = event.request.clone();
        
        return fetch(fetchRequest).then(
          response => {
            // Verificar se recebemos uma resposta válida
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone da resposta
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                // Adicionar requisição ao cache para uso futuro
                cache.put(event.request, responseToCache);
              });
            
            return response;
          }
        );
      })
  );
});

// Gerenciar sincronizações em background (útil para transações offline)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-transactions') {
    event.waitUntil(syncTransactions());
  }
});

// Função para sincronizar transações quando voltar online
async function syncTransactions() {
  try {
    // Aqui seria implementada a lógica para enviar transações pendentes ao servidor
    console.log('Sincronizando transações pendentes');
    
    // Por exemplo, buscar transações pendentes do IndexedDB
    // e enviá-las para a API quando estiver online
    
    return true;
  } catch (error) {
    console.error('Erro ao sincronizar transações:', error);
    return false;
  }
} 