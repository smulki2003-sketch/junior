import { useMemo, useState } from "react";

export function useTable(data = [], { initialPageSize = 10, initialSortKey = "" } = {}) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [sortKey, setSortKey] = useState(initialSortKey);
  const [sortDirection, setSortDirection] = useState("asc");
  const [selectedIds, setSelectedIds] = useState([]);

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    return [...data].sort((a, b) => {
      const aVal = a?.[sortKey];
      const bVal = b?.[sortKey];
      if (aVal === bVal) return 0;
      if (sortDirection === "asc") return aVal > bVal ? 1 : -1;
      return aVal < bVal ? 1 : -1;
    });
  }, [data, sortDirection, sortKey]);

  const total = sorted.length;
  const paged = sorted.slice((page - 1) * pageSize, page * pageSize);

  function toggleSort(nextKey) {
    if (nextKey === sortKey) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(nextKey);
      setSortDirection("asc");
    }
  }

  function toggleSelect(id) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function toggleSelectAll(visibleRows) {
    const ids = visibleRows.map((row) => row.id);
    const allSelected = ids.every((id) => selectedIds.includes(id));
    if (allSelected) {
      setSelectedIds((prev) => prev.filter((id) => !ids.includes(id)));
    } else {
      setSelectedIds((prev) => [...new Set([...prev, ...ids])]);
    }
  }

  return {
    page,
    setPage,
    pageSize,
    setPageSize,
    total,
    sortKey,
    sortDirection,
    toggleSort,
    selectedIds,
    setSelectedIds,
    toggleSelect,
    toggleSelectAll,
    rows: paged,
  };
}

