#!/usr/bin/perl -w

use strict;
use File::Basename;

sub main {
	my ($logFile, @f, @bx, @b, $i, $j, $n);

	$logFile = $ARGV[0] or die "Usage: $0 [log_file]\n";

	open(INFILE, $logFile) or die "$logFile: $!\n";
	@f = <INFILE>;
	close(INFILE);
	chomp @f;

	open(INFILE, "$logFile.sed") or die "$logFile.sed: $!\n";
	@bx = <INFILE>;
	close(INFILE);
	chomp @bx;

	$n = $#f;

	for ($i = 0; $i <= $n; $i++) {
		$b[$i] = basename($bx[$i]);
	}

	for ($i = 0; $i < $n; $i++) {
		for ($j = $i + 1; $j <= $n; $j++) {
			if ($b[$i] eq $b[$j]) {
				# print "cmp.sh -d t \$f[$i] \$f[$j]\n";
				system("cmp.sh -d t \"$f[$i]\" \"$f[$j]\"");
			}
			if ($i % 100 == 0 && $j % 1000 == 0) {
				print "i=$i, j=$j lines compared\n";
			}
		}
	}
}

main();
