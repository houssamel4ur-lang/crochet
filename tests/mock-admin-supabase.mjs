// Test-only Supabase replacement for the static admin. Never deployed or used by production admin.
// Served in place of the jsDelivr UMD build, so it sets window.supabase (no ESM export).
const rows = [];
let counter = 0;
window.__mockAdminRows = rows;
class Query {
  constructor(table) { this.table = table; this.where = []; this.operation = 'read'; this.payload = null; }
  select() { return this; }
  eq(key, val) { this.where.push(row => row[key] === val); return this; }
  in(key, vals) { this.where.push(row => vals.includes(row[key])); return this; }
  order() { return this; }
  maybeSingle() { return this.execute(true); }
  insert(payload) { this.operation = 'insert'; this.payload = payload; return this; }
  update(payload) { this.operation = 'update'; this.payload = payload; return this; }
  delete() { this.operation = 'delete'; return this; }
  async execute(single = false) {
    const source = this.table === 'articles' ? rows : [];
    const matching = source.filter(row => this.where.every(fn => fn(row)));
    if (this.operation === 'insert') {
      const payloads = Array.isArray(this.payload) ? this.payload : [this.payload];
      const created = payloads.map(payload => ({ id: 'test-id-' + (++counter), created_at: new Date().toISOString(), ...payload }));
      if (this.table === 'articles') rows.push(...created);
      return { data: created, error: null };
    }
    if (this.operation === 'update') {
      for (const row of matching) Object.assign(row, this.payload);
      return { data: matching, error: null };
    }
    if (this.operation === 'delete') {
      for (const row of matching) {
        const index = source.indexOf(row);
        if (index !== -1) source.splice(index, 1);
      }
      return { data: matching, error: null };
    }
    return { data: single ? (matching[0] || null) : matching, error: null };
  }
  then(resolve, reject) { return this.execute().then(resolve, reject); }
}
const ownerSession = {
  access_token: 'mock-token',
  user: { id: 'fake-owner', email: 'houssam.el.4ur@gmail.com' }
};
window.supabase = {
  createClient() {
    return {
      auth: {
        getSession: async () => ({ data: { session: ownerSession }, error: null }),
        signInWithPassword: async () => ({ data: { session: ownerSession }, error: null }),
        signOut: async () => ({ error: null })
      },
      rpc: async (name) => {
        if (name === 'is_super_admin') return { data: true, error: null };
        return { data: null, error: null };
      },
      from: table => new Query(table)
    };
  }
};
