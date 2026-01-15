# /db - Database Status and Queries

Check database connectivity and run read-only queries against the myashes PostgreSQL database.

## Connection Details

- **Host**: `platform-postgres-rw.data-platform.svc.cluster.local`
- **Database**: `myashes`
- **User**: `myashes`

## Instructions

### Check Database Connectivity

Use `mcp__kubernetes__exec_in_pod` to run a connectivity test:
- Find a myashes-backend pod first using kubectl_get
- Execute: `["python", "-c", "from app.db.session import SessionLocal; s = SessionLocal(); print('DB Connected:', s.execute('SELECT 1').scalar()); s.close()"]`

### Common Read-Only Queries

Ask user what they want to check, options include:

1. **Table row counts**:
   ```sql
   SELECT 'builds' as table_name, COUNT(*) FROM builds
   UNION ALL SELECT 'build_votes', COUNT(*) FROM build_votes
   UNION ALL SELECT 'feedback', COUNT(*) FROM feedback
   UNION ALL SELECT 'search_analytics', COUNT(*) FROM search_analytics;
   ```

2. **Recent builds**:
   ```sql
   SELECT id, name, class, created_at FROM builds ORDER BY created_at DESC LIMIT 10;
   ```

3. **Vote statistics**:
   ```sql
   SELECT build_id, COUNT(*) as votes, AVG(value) as avg_rating
   FROM build_votes GROUP BY build_id ORDER BY votes DESC LIMIT 10;
   ```

4. **Recent feedback**:
   ```sql
   SELECT rating, search_mode, created_at FROM feedback ORDER BY created_at DESC LIMIT 10;
   ```

5. **Popular search queries**:
   ```sql
   SELECT query, COUNT(*) as count FROM search_analytics
   GROUP BY query ORDER BY count DESC LIMIT 10;
   ```

## Execution

Run queries via kubectl exec into a pod or direct psql if available:
```bash
kubectl exec -it platform-postgres-3 -n data-platform -- psql -U myashes -d myashes -c "YOUR_QUERY"
```

## Safety

- **READ-ONLY queries only** - Never run UPDATE, DELETE, INSERT, or DDL
- Always show query to user before execution
- Report results in a formatted table
