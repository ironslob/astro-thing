import { SearchSkeleton } from "./LoadingState";

export function Typeahead<T>({
  inputId,
  label,
  placeholder,
  query,
  onQuery,
  loading,
  results,
  getKey,
  getLabel,
  getHint,
  getImage,
  onPick,
}: {
  inputId: string;
  label: string;
  placeholder: string;
  query: string;
  onQuery: (value: string) => void;
  loading: boolean;
  results: T[];
  getKey: (item: T) => string;
  getLabel: (item: T) => string;
  getHint?: (item: T) => string | undefined;
  getImage?: (item: T) => string | undefined;
  onPick: (item: T) => void;
}) {
  return (
    <div>
      <label htmlFor={inputId} className="text-sm text-cream-dim">
        {label}
      </label>
      <input
        id={inputId}
        value={query}
        onChange={(e) => onQuery(e.target.value)}
        placeholder={placeholder}
        className="mt-2 min-h-12 w-full rounded-2xl border border-white/10 bg-night-raised px-4 py-3 text-base outline-none ring-amber focus:ring-2"
        autoComplete="off"
      />
      {loading && <SearchSkeleton />}
      {!loading && results.length > 0 && (
        <ul className="mt-2 overflow-hidden rounded-2xl bg-night-card">
          {results.map((item) => {
            const thumb = getImage?.(item);
            return (
              <li key={getKey(item)}>
                <button
                  type="button"
                  className="flex min-h-12 w-full items-center gap-3 px-4 py-3 text-left hover:bg-white/5"
                  onClick={() => onPick(item)}
                >
                  {thumb ? (
                    <img
                      src={thumb}
                      alt=""
                      width={40}
                      height={40}
                      className="h-10 w-10 shrink-0 rounded-lg object-cover"
                    />
                  ) : null}
                  <span>
                    <span>{getLabel(item)}</span>
                    {getHint?.(item) && (
                      <span className="mt-0.5 block text-sm text-cream-dim">{getHint(item)}</span>
                    )}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
