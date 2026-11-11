/** Single screen-registration boundary. Feature modules register here during integration. */
export const screenIds=Object.freeze(['overview','computer','markets','calendar','photos','assistant']);
export function createRegistry(entries) {
 const registry=new Map();
 for(const [id,component] of Object.entries(entries)) {
  if(!screenIds.includes(id)||typeof component!=='function') throw new TypeError('Invalid screen registration');
  registry.set(id,component);
 }
 return id=>registry.get(id);
}
