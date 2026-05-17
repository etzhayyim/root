package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

type depsDriftReport struct {
	RepoRoot         string   `json:"repo_root"`
	DepsIgnoreFile   string   `json:"depsignore_file,omitempty"`
	DepsFiles        []string `json:"deps_files"`
	UndeclaredFiles  []string `json:"undeclared_files"`
	UndeclaredDirs   []string `json:"undeclared_dirs"`
	MissingFiles     []string `json:"missing_files"`
	MissingDirs      []string `json:"missing_dirs"`
	CoveredFiles     int      `json:"covered_files"`
	CoveredDirs      int      `json:"covered_dirs"`
	DeclaredMatchers int      `json:"declared_matchers"`
}

func (r depsDriftReport) HasDrift() bool {
	return len(r.UndeclaredFiles) > 0 || len(r.UndeclaredDirs) > 0 || len(r.MissingFiles) > 0 || len(r.MissingDirs) > 0
}

type depsIgnorePattern struct {
	raw         string
	dirOnly     bool
	hasSlash    bool
	pathRegex   *regexp.Regexp
	nameRegex   *regexp.Regexp
	prefixRegex *regexp.Regexp
}

type depsDeclaredMatcher struct {
	path    string
	section string
	source  string
	dirOnly bool
	regex   *regexp.Regexp
}

func runDepsDrift(args []string) error {
	fs := flag.NewFlagSet("deps drift", flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	format := fs.String("format", "text", "output format: text|json")
	limit := fs.Int("limit", 50, "max items to print per section in text output (0 = unlimited)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *format != "text" && *format != "json" {
		return fmt.Errorf("unsupported format %q (want text or json)", *format)
	}
	if fs.NArg() != 0 {
		return fmt.Errorf("unexpected args: %s", strings.Join(fs.Args(), " "))
	}

	root, err := findGitRoot(".")
	if err != nil {
		return err
	}
	report, err := collectDepsDrift(root)
	if err != nil {
		return err
	}

	switch *format {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		if err := enc.Encode(report); err != nil {
			return fmt.Errorf("encode drift report: %w", err)
		}
	default:
		printDepsDriftText(report, *limit)
	}

	if report.HasDrift() {
		return fmt.Errorf("deps drift detected")
	}
	return nil
}

func printDepsDriftText(report depsDriftReport, limit int) {
	fmt.Printf("deps drift report\n")
	fmt.Printf("repo: %s\n", report.RepoRoot)
	if report.DepsIgnoreFile != "" {
		fmt.Printf("depsignore: %s\n", report.DepsIgnoreFile)
	}
	fmt.Printf("deps.toml files: %d\n", len(report.DepsFiles))
	fmt.Printf("declared matchers: %d\n", report.DeclaredMatchers)
	fmt.Printf("covered actual paths: files=%d dirs=%d\n", report.CoveredFiles, report.CoveredDirs)
	fmt.Printf("drift: undeclared_files=%d undeclared_dirs=%d missing_files=%d missing_dirs=%d\n",
		len(report.UndeclaredFiles), len(report.UndeclaredDirs), len(report.MissingFiles), len(report.MissingDirs))

	printDepsDriftSection("undeclared files", report.UndeclaredFiles, limit)
	printDepsDriftSection("undeclared dirs", report.UndeclaredDirs, limit)
	printDepsDriftSection("declared but missing files", report.MissingFiles, limit)
	printDepsDriftSection("declared but missing dirs", report.MissingDirs, limit)
}

func printDepsDriftSection(title string, values []string, limit int) {
	fmt.Printf("\n%s\n", title)
	if len(values) == 0 {
		fmt.Printf("  none\n")
		return
	}
	display := values
	if limit > 0 && len(display) > limit {
		display = display[:limit]
	}
	for _, value := range display {
		fmt.Printf("  - %s\n", value)
	}
	if len(display) < len(values) {
		fmt.Printf("  ... %d more\n", len(values)-len(display))
	}
}

func collectDepsDrift(root string) (depsDriftReport, error) {
	ignorePath := filepath.Join(root, ".depsignore")
	ignorePatterns, err := loadDepsIgnore(ignorePath)
	if err != nil {
		return depsDriftReport{}, err
	}

	actualFiles, actualDirs, depsFiles, err := walkRepoPaths(root, ignorePatterns)
	if err != nil {
		return depsDriftReport{}, err
	}

	matchers, err := collectDeclaredMatchers(root, depsFiles)
	if err != nil {
		return depsDriftReport{}, err
	}
	matchers = filterIgnoredMatchers(matchers, ignorePatterns)

	actualDirSet := make(map[string]struct{}, len(actualDirs))
	for _, path := range actualDirs {
		actualDirSet[path] = struct{}{}
	}

	coveredFiles, undeclaredFiles := matchActualPaths(actualFiles, matchers, actualDirSet, false)
	coveredDirs, undeclaredDirs := matchActualPaths(actualDirs, matchers, actualDirSet, true)
	missingFiles, missingDirs := findMissingDeclaredPaths(actualFiles, actualDirs, matchers)

	report := depsDriftReport{
		RepoRoot:         root,
		DepsIgnoreFile:   ignorePath,
		DepsFiles:        depsFiles,
		UndeclaredFiles:  undeclaredFiles,
		UndeclaredDirs:   undeclaredDirs,
		MissingFiles:     missingFiles,
		MissingDirs:      missingDirs,
		CoveredFiles:     coveredFiles,
		CoveredDirs:      coveredDirs,
		DeclaredMatchers: len(matchers),
	}
	return report, nil
}

func walkRepoPaths(root string, ignorePatterns []depsIgnorePattern) ([]string, []string, []string, error) {
	var files []string
	var dirs []string
	var depsFiles []string
	err := filepath.WalkDir(root, func(path string, d os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == root {
			return nil
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return err
		}
		rel = toSlashPath(rel)
		if matchesDepsIgnore(rel, d.IsDir(), ignorePatterns) {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		if d.IsDir() {
			dirs = append(dirs, rel)
			return nil
		}
		if filepath.Base(path) == "deps.toml" {
			depsFiles = append(depsFiles, rel)
			return nil
		}
		if rel == ".depsignore" {
			return nil
		}
		files = append(files, rel)
		return nil
	})
	if err != nil {
		return nil, nil, nil, err
	}
	sort.Strings(files)
	sort.Strings(dirs)
	sort.Strings(depsFiles)
	return files, dirs, depsFiles, nil
}

func loadDepsIgnore(path string) ([]depsIgnorePattern, error) {
	src, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("read %s: %w", path, err)
	}

	lines := strings.Split(string(src), "\n")
	patterns := make([]depsIgnorePattern, 0, len(lines))
	for _, rawLine := range lines {
		line := stripDepsIgnoreComment(rawLine)
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		dirOnly := strings.HasSuffix(line, "/")
		if dirOnly {
			line = strings.TrimSuffix(line, "/")
		}
		if line == "" {
			continue
		}
		pattern, err := compileDepsIgnorePattern(line, dirOnly)
		if err != nil {
			return nil, fmt.Errorf("parse .depsignore pattern %q: %w", line, err)
		}
		patterns = append(patterns, pattern)
	}
	return patterns, nil
}

func stripDepsIgnoreComment(line string) string {
	inPattern := false
	for idx, r := range line {
		if r == '#' && !inPattern {
			return strings.TrimSpace(line[:idx])
		}
		if r == '#' {
			return strings.TrimSpace(line[:idx])
		}
		if !inPattern && r != ' ' && r != '\t' {
			inPattern = true
		}
		if inPattern && r == ' ' {
			rest := strings.TrimSpace(line[idx:])
			if strings.HasPrefix(rest, "#") {
				return strings.TrimSpace(line[:idx])
			}
		}
	}
	return strings.TrimSpace(line)
}

func compileDepsIgnorePattern(pattern string, dirOnly bool) (depsIgnorePattern, error) {
	hasSlash := strings.Contains(pattern, "/")
	entry := depsIgnorePattern{
		raw:      pattern,
		dirOnly:  dirOnly,
		hasSlash: hasSlash,
	}
	if hasSlash {
		rx, err := compilePathGlob(pattern)
		if err != nil {
			return depsIgnorePattern{}, err
		}
		entry.pathRegex = rx
		if dirOnly {
			entry.prefixRegex = rx
		}
		return entry, nil
	}
	rx, err := compileNameGlob(pattern)
	if err != nil {
		return depsIgnorePattern{}, err
	}
	entry.nameRegex = rx
	return entry, nil
}

func matchesDepsIgnore(path string, isDir bool, patterns []depsIgnorePattern) bool {
	for _, pattern := range patterns {
		if pattern.dirOnly {
			if pattern.hasSlash {
				for _, prefix := range pathDirPrefixes(path, isDir) {
					if pattern.prefixRegex.MatchString(prefix) {
						return true
					}
				}
				continue
			}
			for _, segment := range pathSegments(path, isDir) {
				if pattern.nameRegex.MatchString(segment) {
					return true
				}
			}
			continue
		}
		if pattern.hasSlash {
			if pattern.pathRegex.MatchString(path) {
				return true
			}
			continue
		}
		if pattern.nameRegex.MatchString(pathBase(path)) {
			return true
		}
	}
	return false
}

func pathSegments(path string, isDir bool) []string {
	parts := strings.Split(path, "/")
	if isDir {
		return parts
	}
	if len(parts) <= 1 {
		return parts[:0]
	}
	return parts[:len(parts)-1]
}

func pathDirPrefixes(path string, isDir bool) []string {
	parts := strings.Split(path, "/")
	limit := len(parts)
	if !isDir {
		limit--
	}
	if limit <= 0 {
		return nil
	}
	out := make([]string, 0, limit)
	for i := 1; i <= limit; i++ {
		out = append(out, strings.Join(parts[:i], "/"))
	}
	return out
}

func pathBase(path string) string {
	idx := strings.LastIndex(path, "/")
	if idx < 0 {
		return path
	}
	return path[idx+1:]
}

func collectDeclaredMatchers(root string, depsFiles []string) ([]depsDeclaredMatcher, error) {
	var matchers []depsDeclaredMatcher
	for _, rel := range depsFiles {
		full := filepath.Join(root, filepath.FromSlash(rel))
		sections, err := parseDepsSectionsWithTomllib(full)
		if err != nil {
			return nil, fmt.Errorf("parse %s: %w", rel, err)
		}
		baseDir := filepath.Dir(rel)
		if baseDir == "." {
			baseDir = ""
		}

		addMatchers := func(section string, dirOnly bool) error {
			for _, key := range sections[section] {
				matcher, err := newDeclaredMatcher(baseDir, key, section, rel, dirOnly)
				if err != nil {
					return err
				}
				matchers = append(matchers, matcher)
			}
			return nil
		}

		if err := addMatchers("files", false); err != nil {
			return nil, err
		}
		if err := addMatchers("subdirs", true); err != nil {
			return nil, err
		}
		if err := addMatchers("standalone", true); err != nil {
			return nil, err
		}
		if err := addMatchers("layers", true); err != nil {
			return nil, err
		}
	}
	sort.Slice(matchers, func(i, j int) bool {
		if matchers[i].path == matchers[j].path {
			return matchers[i].source < matchers[j].source
		}
		return matchers[i].path < matchers[j].path
	})
	return matchers, nil
}

func filterIgnoredMatchers(matchers []depsDeclaredMatcher, ignorePatterns []depsIgnorePattern) []depsDeclaredMatcher {
	filtered := make([]depsDeclaredMatcher, 0, len(matchers))
	for _, matcher := range matchers {
		if matchesDepsIgnore(matcher.path, matcher.dirOnly, ignorePatterns) {
			continue
		}
		if !matcher.dirOnly && matchesDepsIgnore(matcher.path, true, ignorePatterns) {
			continue
		}
		filtered = append(filtered, matcher)
	}
	return filtered
}

func parseDepsSectionsWithTomllib(path string) (map[string][]string, error) {
	script := strings.Join([]string{
		"import json, sys, tomllib",
		"with open(sys.argv[1], 'rb') as f:",
		"    data = tomllib.load(f)",
		"out = {}",
		"for section in ('files', 'subdirs', 'standalone', 'layers'):",
		"    value = data.get(section, {})",
		"    out[section] = sorted(value.keys()) if isinstance(value, dict) else []",
		"print(json.dumps(out))",
	}, "\n")
	cmd := exec.Command("python3", "-c", script, path)
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}
	var sections map[string][]string
	if err := json.Unmarshal(output, &sections); err != nil {
		return nil, fmt.Errorf("decode tomllib output: %w", err)
	}
	return sections, nil
}

func newDeclaredMatcher(baseDir, key, section, source string, dirOnly bool) (depsDeclaredMatcher, error) {
	path := toSlashPath(filepath.Join(baseDir, filepath.FromSlash(key)))
	regex, err := compilePathGlob(path)
	if err != nil {
		return depsDeclaredMatcher{}, fmt.Errorf("%s [%s.%q]: %w", source, section, key, err)
	}
	return depsDeclaredMatcher{
		path:    path,
		section: section,
		source:  source,
		dirOnly: dirOnly,
		regex:   regex,
	}, nil
}

func matchActualPaths(actual []string, matchers []depsDeclaredMatcher, actualDirSet map[string]struct{}, wantDir bool) (int, []string) {
	covered := 0
	var missing []string
	for _, path := range actual {
		if declaredPathMatches(path, wantDir, matchers, actualDirSet) {
			covered++
			continue
		}
		missing = append(missing, path)
	}
	return covered, missing
}

func declaredPathMatches(path string, isDir bool, matchers []depsDeclaredMatcher, actualDirSet map[string]struct{}) bool {
	for _, matcher := range matchers {
		if matcher.regex.MatchString(path) {
			return true
		}
		if pathCoveredByDeclaredDir(path, matcher, actualDirSet) {
			return true
		}
	}
	return false
}

func pathCoveredByDeclaredDir(path string, matcher depsDeclaredMatcher, actualDirSet map[string]struct{}) bool {
	if hasGlobMeta(matcher.path) {
		return false
	}
	if matcher.dirOnly {
		return path == matcher.path || strings.HasPrefix(path, matcher.path+"/")
	}
	if _, ok := actualDirSet[matcher.path]; ok {
		return path == matcher.path || strings.HasPrefix(path, matcher.path+"/")
	}
	return false
}

func findMissingDeclaredPaths(actualFiles, actualDirs []string, matchers []depsDeclaredMatcher) ([]string, []string) {
	fileSet := make(map[string]struct{}, len(actualFiles))
	for _, path := range actualFiles {
		fileSet[path] = struct{}{}
	}
	dirSet := make(map[string]struct{}, len(actualDirs))
	for _, path := range actualDirs {
		dirSet[path] = struct{}{}
	}

	var missingFiles []string
	var missingDirs []string
	seenFiles := map[string]struct{}{}
	seenDirs := map[string]struct{}{}
	for _, matcher := range matchers {
		if matcherMatchesSet(matcher, actualFiles, actualDirs) {
			continue
		}
		if matcher.dirOnly {
			if _, ok := seenDirs[matcher.path]; ok {
				continue
			}
			seenDirs[matcher.path] = struct{}{}
			if _, exists := dirSet[matcher.path]; !exists || hasGlobMeta(matcher.path) {
				missingDirs = append(missingDirs, matcher.path)
			}
			continue
		}
		if _, ok := seenFiles[matcher.path]; ok {
			continue
		}
		seenFiles[matcher.path] = struct{}{}
		if _, fileExists := fileSet[matcher.path]; fileExists && !hasGlobMeta(matcher.path) {
			continue
		}
		if _, dirExists := dirSet[matcher.path]; dirExists && !hasGlobMeta(matcher.path) {
			continue
		}
		missingFiles = append(missingFiles, matcher.path)
	}
	sort.Strings(missingFiles)
	sort.Strings(missingDirs)
	return missingFiles, missingDirs
}

func matcherMatchesSet(matcher depsDeclaredMatcher, actualFiles, actualDirs []string) bool {
	if matcher.dirOnly {
		for _, path := range actualDirs {
			if matcher.regex.MatchString(path) {
				return true
			}
		}
		return false
	}
	for _, path := range actualFiles {
		if matcher.regex.MatchString(path) {
			return true
		}
	}
	for _, path := range actualDirs {
		if matcher.regex.MatchString(path) {
			return true
		}
	}
	return false
}

func compilePathGlob(pattern string) (*regexp.Regexp, error) {
	return regexp.Compile("^" + globToRegex(pattern) + "$")
}

func compileNameGlob(pattern string) (*regexp.Regexp, error) {
	return regexp.Compile("^" + globToRegex(pattern) + "$")
}

func globToRegex(pattern string) string {
	var b strings.Builder
	for i := 0; i < len(pattern); {
		switch pattern[i] {
		case '*':
			if i+1 < len(pattern) && pattern[i+1] == '*' {
				if i+2 < len(pattern) && pattern[i+2] == '/' {
					b.WriteString("(?:.*/)?")
					i += 3
					continue
				}
				b.WriteString(".*")
				i += 2
				continue
			}
			b.WriteString("[^/]*")
		case '?':
			b.WriteString("[^/]")
		case '.', '+', '(', ')', '|', '^', '$', '{', '}', '[', ']', '\\':
			b.WriteByte('\\')
			b.WriteByte(pattern[i])
		default:
			b.WriteByte(pattern[i])
		}
		i++
	}
	return b.String()
}

func hasGlobMeta(value string) bool {
	return strings.ContainsAny(value, "*?[")
}

func toSlashPath(path string) string {
	return filepath.ToSlash(filepath.Clean(path))
}
