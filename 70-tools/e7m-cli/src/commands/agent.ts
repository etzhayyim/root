import { Command } from 'commander';
import { execa } from 'execa';
import { resolveApp } from '../lib/root.js';

async function targetDirFor(project?: string): Promise<string> {
  if (!project) return process.cwd();
  return resolveApp(project);
}

async function runLangGraph(sub: 'dev' | 'build' | 'up', project: string | undefined, emoji: string, label: string): Promise<void> {
  const cwd = await targetDirFor(project);
  console.log(`${emoji} LangGraph ${label} (${project ?? cwd})`);
  try {
    await execa('npx', ['@langchain/langgraph-cli', sub], { cwd, stdio: 'inherit' });
  } catch (err) {
    console.error(`LangGraph ${sub} failed.`, err);
    process.exit(1);
  }
}

export const agentCmd = new Command('agent').description('Manage LangGraph AI Agents');

agentCmd
  .command('dev [project]')
  .description('Start LangGraph development server and LangGraph Studio')
  .action((project?: string) => runLangGraph('dev', project, '>>', 'dev'));

agentCmd
  .command('build [project]')
  .description('Build LangGraph application')
  .action((project?: string) => runLangGraph('build', project, '>>', 'build'));

agentCmd
  .command('up [project]')
  .description('Deploy LangGraph application to local Docker')
  .action((project?: string) => runLangGraph('up', project, '>>', 'up'));
