// Fixture Go cobra app for the yorishiro source-repo extractor tests.
//
// Run:
//   python3 70-tools/etzhayyim-cli/yorishiro/scripts/extract-cobra.py \
//       70-tools/etzhayyim-cli/yorishiro/fixtures/source-repo-cobra \
//       --kami-id bin:cobra-demo --binary cobra-demo
//
// Not a working Go program — fixture-only.

package main

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "cobra-demo",
	Short: "Demo cobra CLI used by the yorishiro source-repo fixture.",
	Long:  "Longer description of the cobra demo CLI.",
}

var greetCmd = &cobra.Command{
	Use:   "greet",
	Short: "Print a greeting.",
	Long:  "Print a greeting for NAME with optional shouting.",
}

var renderCmd = &cobra.Command{
	Use:   "render",
	Short: "Render output to file or stdout.",
}

func init() {
	rootCmd.PersistentFlags().BoolVar(&verbose, "verbose", false, "Enable verbose logging.")
	rootCmd.PersistentFlags().StringVar(&config, "config", "/etc/cobra-demo.yaml", "Path to config file.")

	greetCmd.Flags().BoolVarP(&shout, "shout", "s", false, "Uppercase the greeting.")
	greetCmd.Flags().StringVar(&lang, "lang", "en", "Language code (en|jp).")
	greetCmd.Args = cobra.ExactArgs(1)

	renderCmd.Flags().Int64Var(&maxRows, "max-rows", 100, "Maximum rows.")
	renderCmd.Flags().Float64Var(&quality, "quality", 0.9, "Quality multiplier.")
	renderCmd.Args = cobra.MinimumNArgs(1)

	rootCmd.AddCommand(greetCmd)
	rootCmd.AddCommand(renderCmd)
}

var (
	verbose bool
	config  string
	shout   bool
	lang    string
	maxRows int64
	quality float64
)

func main() {
	_ = rootCmd.Execute()
}
