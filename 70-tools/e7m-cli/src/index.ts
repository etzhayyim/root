import { Command } from 'commander';
import { agentCmd } from './commands/agent.js';
import { actorCmd } from './commands/actor.js';
import { contractCmd } from './commands/contract.js';
import { graphCmd } from './commands/graph.js';
import { devCmd } from './commands/dev.js';

const program = new Command();

program
  .name('e7m')
  .description('Etzhayyim Monorepo Unified CLI')
  .version('0.1.0');

// Register commands
program.addCommand(agentCmd);
program.addCommand(actorCmd);
program.addCommand(contractCmd);
program.addCommand(graphCmd);
program.addCommand(devCmd);

program.parse(process.argv);
